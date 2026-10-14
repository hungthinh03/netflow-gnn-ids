"""Pydantic schemas: hợp đồng request/response của REST API.

Không đặt truy vấn DB hoặc gọi GNN trong file này. Khi API ổn định, frontend và
backend cùng dựa vào các schema này để tránh lệch tên trường/kiểu dữ liệu.
"""
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

PredictionLabel = Literal["benign", "attack", "unknown"]
PredictionMode = Literal["mock", "model"]


class FlowFeatures(BaseModel):
    """Các trường tối thiểu của một flow đầu vào.

    TODO(model): thay/bổ sung trường theo feature schema thực tế. Nếu model dùng
    91 features, nên tạo một schema/version rõ ràng và kiểm tra đúng thứ tự cột
    trong prediction_service; không suy ra 91 features từ các trường dashboard.
    """
    src: IPvAnyAddress
    dst: IPvAnyAddress
    proto: str = Field(min_length=1, max_length=16)
    port: int = Field(ge=0, le=65535)
    bytes: int = Field(ge=0)
    pkts: int = Field(ge=0)
    dur: float = Field(ge=0)
    ttl: int | None = Field(default=None, ge=0, le=255)
    retrans: int | None = Field(default=None, ge=0)
    iat: float | None = Field(default=None, ge=0)


class PredictionRequest(BaseModel):
    flow: FlowFeatures
    # Dành cho các model GNN cần graph snapshot hoặc thời điểm tham chiếu.
    snapshot_id: int | None = None
    timestamp: datetime | None = None


class PredictionResult(BaseModel):
    flow_id: int | None = None
    label: PredictionLabel
    # score là điểm số model; chỉ gọi là xác suất khi đầu ra đã được kiểm tra/calibrate.
    score: float | None = Field(default=None, ge=0, le=1)
    attack_family: str | None = None
    threshold: float | None = Field(default=None, ge=0, le=1)
    mode: PredictionMode
    model_name: str | None = None
    model_version: str | None = None
    explanation: str | None = None


class FlowRead(BaseModel):
    """Flow đã lưu và các trường dự đoán dùng bởi dashboard."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime | None = None
    src: str
    dst: str
    proto: str
    port: int
    bytes: int = 0
    pkts: int = 0
    dur: float = 0
    ttl: int | None = None
    flags: str | None = None
    retrans: int | None = None
    iat: float | None = None
    score: float | None = None
    prediction: PredictionLabel = "unknown"
    attack_family: str | None = None
    feedback_label: PredictionLabel | None = None


class FlowListResponse(BaseModel):
    mode: PredictionMode
    items: list[FlowRead]
    total: int
    window: str


class ModelStatusResponse(BaseModel):
    mode: PredictionMode
    ready: bool
    model_name: str | None = None
    model_version: str | None = None
    message: str


class FeedbackRequest(BaseModel):
    # unset dùng khi gỡ phản hồi đã ghi trước đó.
    label: Literal["benign", "attack", "unset"]
    note: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    flow_id: int
    label: str
    saved: bool
    message: str


class BlocklistCreate(BaseModel):
    ip: IPvAnyAddress
    scope: Literal["block", "isolate"] = "block"
    reason: str = Field(min_length=1, max_length=1000)
    duration_s: int = Field(default=86400, ge=0)
    flow_id: int | None = None


class BlocklistRead(BaseModel):
    ip: str
    scope: Literal["block", "isolate"]
    reason: str
    duration_s: int
    created_at: datetime | None = None
    expires_at: datetime | None = None
    active: bool = True


class BlocklistResponse(BaseModel):
    items: list[BlocklistRead]
    total: int


class StatsResponse(BaseModel):
    window: str
    total_flows: int
    attack_flows: int
    benign_flows: int
    unknown_flows: int
    attack_rate: float | None = None
    # Không đưa metric huấn luyện cố định vào đây; các metric đánh giá phải lấy từ
    # báo cáo đánh giá model/test set, không phải tính từ flow live.


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
    context: dict[str, Any] | None = None
