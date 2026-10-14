
from typing import Literal
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="NetFlow GNN IDS API")

# Chuyển sang "model" khi đã tích hợp predictor thật.
MODE = "mock"


class FlowInput(BaseModel):
    src: str
    dst: str
    proto: str
    port: int = Field(ge=0, le=65535)
    bytes: int = Field(ge=0)
    pkts: int = Field(ge=0)
    dur: float = Field(ge=0)
    ttl: int = Field(ge=0, le=255)
    retrans: int = Field(ge=0)
    iat: float = Field(ge=0)


class FeedbackInput(BaseModel):
    label: Literal["benign", "attack", "unset"]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/model/status")
def model_status():
    return {
        "mode": MODE,
        "ready": MODE == "model",
        "model_name": "mock_predictor" if MODE == "mock" else "gnn"
    }


@app.get("/api/flows")
def get_flows(
    window: Literal["5m", "30m", "1h"] = Query("30m")
):
    # TODO: đọc từ flow_service / kho dữ liệu
    # Không tự tạo kết quả dự đoán thật ở endpoint này.
    return {
        "mode": MODE,
        "items": [],
        "total": 0
    }


@app.post("/api/predict")
def predict_flow(flow: FlowInput):
    if MODE != "model":
        raise HTTPException(
            status_code=503,
            detail="Chưa có mô hình GNN; API dự đoán thật chưa sẵn sàng."
        )

    # TODO:
    # 1. Chuyển FlowInput thành đúng schema đã huấn luyện.
    # 2. Tạo graph/context nếu kiến trúc GNN yêu cầu.
    # 3. Gọi prediction_service.
    # 4. Trả prediction và attack score.
    raise HTTPException(
        status_code=501,
        detail="GNN inference chưa được triển khai."
    )


@app.post("/api/flows/{flow_id}/feedback")
def feedback(flow_id: int, body: FeedbackInput):
    # TODO: lưu phản hồi vào database hoặc kho feedback.
    return {
        "flow_id": flow_id,
        "label": body.label,
        "saved": False,
        "message": "Chưa cấu hình lưu feedback."
    }
