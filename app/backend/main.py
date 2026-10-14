
import os
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Các service này cần được tạo trong thư mục services/.
# Chúng không nên chứa logic xử lý HTTP hoặc phụ thuộc trực tiếp vào FastAPI.
from app.backend.services.flow_service import FlowService
from app.backend.services.prediction_service import PredictionService
from app.backend.services.alert_service import AlertService


# Đọc cấu hình từ môi trường.
# MOCK là chế độ phát triển; MODEL chỉ dùng khi predictor thật đã được cấu hình.
APP_MODE = os.getenv("IDS_MODE", "mock").lower()

if APP_MODE not in {"mock", "model"}:
    raise RuntimeError("IDS_MODE phải là 'mock' hoặc 'model'.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Khởi tạo các thành phần dùng chung khi backend khởi động.

    Khi tích hợp hoàn chỉnh:
    - Tạo DB session/repository hoặc connection pool.
    - Nạp checkpoint, feature mapping và scaler nếu dùng GNN.
    - Kiểm tra cấu hình và tài nguyên cần thiết.

    Không nạp lại model ở mỗi request.
    """
    app.state.flow_service = FlowService()
    app.state.prediction_service = PredictionService(mode=APP_MODE)
    app.state.alert_service = AlertService()

    yield

    # Sau này đóng DB pool, giải phóng tài nguyên model nếu cần.
    # Việc đóng kết nối nên được quản lý bởi lifespan/repository tương ứng.


app = FastAPI(
    title="NetFlow GNN IDS API",
    version="0.1.0",
    description="API cho dashboard phát hiện xâm nhập dựa trên NetFlow và Host Graph.",
    lifespan=lifespan,
)

# Chỉ cho phép origin frontend được tin cậy.
# Điều chỉnh danh sách theo địa chỉ frontend thực tế.
frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in frontend_origins],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------- Request schemas ----------

class FlowInput(BaseModel):
    """Đặc trưng flow đầu vào ở lớp API.

    Đây chưa mặc định là schema 91 đặc trưng của GNN.
    PredictionService phải kiểm tra/ánh xạ sang schema model thực tế.
    """
    src: str
    dst: str
    proto: Literal["TCP", "UDP", "ICMP"]
    port: int = Field(ge=0, le=65535)
    bytes: int = Field(ge=0)
    pkts: int = Field(ge=0)
    dur: float = Field(ge=0)
    ttl: int = Field(ge=0, le=255)
    retrans: int = Field(ge=0)
    iat: float = Field(ge=0)


class FeedbackInput(BaseModel):
    """Nhãn phản hồi do người vận hành cung cấp."""
    label: Literal["benign", "attack", "unset"]


# ---------- Health and model status ----------

@app.get("/api/health")
def health():
    """Kiểm tra tiến trình API có đang phục vụ request hay không.

    Đây chưa phải kiểm tra toàn diện DB/model.
    Có thể mở rộng thành readiness check riêng.
    """
    return {"status": "ok"}


@app.get("/api/model/status")
def model_status():
    """Trả trạng thái model để dashboard phân biệt mock và inference thật."""
    service = app.state.prediction_service

    return {
        "mode": APP_MODE,
        "ready": service.is_ready(),
        "model_name": service.model_name(),
        "version": service.model_version(),
    }


# ---------- Flow query ----------

@app.get("/api/flows")
def get_flows(
    window: Literal["5m", "30m", "1h"] = Query("30m"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Lấy flow qua FlowService.

    Khi có DB: service truy vấn flow theo thời gian, lấy prediction đã lưu
    hoặc gọi pipeline inference theo thiết kế triển khai.

    Không nên âm thầm tạo dữ liệu giả trong endpoint production.
    """
    try:
        result = app.state.flow_service.list_flows(
            window=window,
            limit=limit,
        )
        return result
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="FlowService chưa được kết nối với kho dữ liệu.",
        )


# ---------- Prediction ----------

@app.post("/api/predict")
def predict_flow(flow: FlowInput):
    """Dự đoán flow.

    Mock mode có thể trả kết quả demo được đánh dấu rõ.
    Model mode phải gọi GNN thật, không được tự sinh score giả.
    """
    service = app.state.prediction_service

    if not service.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Predictor chưa sẵn sàng.",
        )

    try:
        return service.predict_flow(flow.model_dump())
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Inference chưa được triển khai.",
        )


# ---------- Feedback ----------

@app.post("/api/flows/{flow_id}/feedback")
def feedback(flow_id: int, body: FeedbackInput):
    """Ghi nhận phản hồi qua AlertService.

    Khi có DB: lưu người phản hồi, nhãn, thời gian và prediction liên quan.
    Feedback không tự động trở thành nhãn huấn luyện đáng tin cậy.
    """
    try:
        result = app.state.alert_service.record_feedback(
            flow_id=flow_id,
            label=body.label,
        )
        return result
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Feedback storage chưa được cấu hình.",
        )
