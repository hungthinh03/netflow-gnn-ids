"""Quản lý cảnh báo và phản hồi người dùng.

Một prediction và một alert không nhất thiết là cùng một bản ghi: prediction là
kết quả suy luận; alert là sự kiện cần theo dõi/xử lý theo chính sách cảnh báo.
"""
from typing import Protocol, Any
from schemas import FeedbackRequest, FeedbackResponse


class AlertRepository(Protocol):
    def get_flow(self, flow_id: int) -> Any | None: ...
    def upsert_feedback(self, flow_id: int, label: str, note: str | None) -> None: ...
    # TODO(db): bổ sung list_alerts, get_alert, update_alert_status và audit log.


class AlertService:
    def __init__(self, repository: AlertRepository):
        self.repository = repository

    def record_feedback(self, flow_id: int, body: FeedbackRequest) -> FeedbackResponse:
        flow = self.repository.get_flow(flow_id)
        if flow is None:
            raise LookupError(f"Không tìm thấy flow id={flow_id}")

        # TODO(db): nên lưu ai phản hồi, thời điểm, nhãn cũ/mới và lý do vào bảng
        # feedback/audit riêng. Feedback KHÔNG tự động cập nhật nhãn train hoặc
        # huấn luyện lại model; cần quy trình xác minh nhãn riêng.
        self.repository.upsert_feedback(flow_id, body.label, body.note)
        return FeedbackResponse(
            flow_id=flow_id, label=body.label, saved=True,
            message="Đã ghi nhận phản hồi; chưa tự động thay đổi model.",
        )
