"""Nghiệp vụ truy vấn và chuẩn hóa flow cho dashboard.

DB adapter chưa được cố định ở đây. Khi PostgreSQL/ORM đã ổn định, truyền vào
một repository có các method được mô tả bên dưới; service không nên tự mở kết
nối DB hay chứa SQL trực tiếp.
"""
from datetime import datetime, timezone
from typing import Protocol, Any
from schemas import FlowListResponse, FlowRead, PredictionMode


class FlowRepository(Protocol):
    """Interface mà adapter SQLAlchemy/PostgreSQL cần triển khai.

    list_flows(since: datetime, limit: int, offset: int) -> tuple[list[Any], int]
    get_flow(flow_id: int) -> Any | None

    TODO(db): implement trong repository riêng, ví dụ repositories/flow_repository.py.
    """
    def list_flows(self, since: datetime, limit: int, offset: int = 0) -> tuple[list[Any], int]: ...
    def get_flow(self, flow_id: int) -> Any | None: ...


WINDOW_SECONDS = {"5m": 300, "30m": 1800, "1h": 3600}


def parse_window(window: str) -> datetime:
    """Đổi cửa sổ cho phép thành thời điểm bắt đầu truy vấn; từ chối giá trị lạ."""
    if window not in WINDOW_SECONDS:
        raise ValueError(f"window không hợp lệ: {window}; chọn một trong {list(WINDOW_SECONDS)}")
    return datetime.now(timezone.utc).replace(microsecond=0) - __import__("datetime").timedelta(seconds=WINDOW_SECONDS[window])


def _to_flow_read(row: Any) -> FlowRead:
    """Map ORM row/record sang schema API.

    TODO(db): đổi mapping cho đúng tên cột trong bảng flows/predictions thực tế.
    Không tự tạo score/label nếu DB chưa có dự đoán; dùng unknown/None.
    """
    get = lambda key, default=None: (row.get(key, default) if isinstance(row, dict) else getattr(row, key, default))
    return FlowRead(
        id=get("id"), timestamp=get("timestamp", get("created_at")),
        src=str(get("src", get("src_ip", "0.0.0.0"))),
        dst=str(get("dst", get("dst_ip", "0.0.0.0"))),
        proto=str(get("proto", get("protocol", "UNKNOWN"))),
        port=int(get("port", get("dst_port", 0))),
        bytes=int(get("bytes", get("bytes_total", 0)) or 0),
        pkts=int(get("pkts", get("packets_total", 0)) or 0),
        dur=float(get("dur", get("duration", 0)) or 0), ttl=get("ttl"),
        flags=get("flags"), retrans=get("retrans"), iat=get("iat"),
        score=get("score", get("attack_score")),
        prediction=get("prediction", get("label", "unknown")) or "unknown",
        attack_family=get("attack_family", get("attack_type")),
        feedback_label=get("feedback_label"),
    )


class FlowService:
    def __init__(self, repository: FlowRepository, mode: PredictionMode = "mock"):
        self.repository = repository
        self.mode = mode

    def list_flows(self, window: str = "30m", limit: int = 500, offset: int = 0) -> FlowListResponse:
        if not 1 <= limit <= 5000:
            raise ValueError("limit phải nằm trong khoảng 1..5000")
        if offset < 0:
            raise ValueError("offset không được âm")
        since = parse_window(window)
        rows, total = self.repository.list_flows(since=since, limit=limit, offset=offset)
        return FlowListResponse(mode=self.mode, items=[_to_flow_read(r) for r in rows], total=total, window=window)

    def get_flow(self, flow_id: int) -> FlowRead | None:
        row = self.repository.get_flow(flow_id)
        return _to_flow_read(row) if row is not None else None
