"""Quản lý blocklist ở tầng ứng dụng.

Lưu IP vào DB chỉ ghi nhận ý định/chính sách. Nó KHÔNG chặn packet thật nếu chưa
kết nối với firewall/SDN/agent thực thi. Tích hợp thực thi cần quyền hạn, audit,
kiểm tra allowlist và xác nhận thao tác nguy hiểm.
"""
from datetime import datetime, timezone
from typing import Protocol, Any
from schemas import BlocklistCreate, BlocklistRead, BlocklistResponse


class BlocklistRepository(Protocol):
    def list_entries(self) -> list[Any]: ...
    def get_active(self, ip: str) -> Any | None: ...
    def create_or_update(self, data: dict) -> Any: ...
    def delete(self, ip: str) -> bool: ...


class BlocklistService:
    def __init__(self, repository: BlocklistRepository):
        self.repository = repository

    def list_entries(self) -> BlocklistResponse:
        rows = self.repository.list_entries()
        # TODO(db): lọc active theo expires_at tại DB; hiện mapping dựa trên record.
        items = [BlocklistRead(
            ip=str(getattr(r, "ip", r.get("ip") if isinstance(r, dict) else "")),
            scope=getattr(r, "scope", r.get("scope", "block") if isinstance(r, dict) else "block"),
            reason=getattr(r, "reason", r.get("reason", "") if isinstance(r, dict) else ""),
            duration_s=int(getattr(r, "duration_s", r.get("duration_s", 0) if isinstance(r, dict) else 0)),
            created_at=getattr(r, "created_at", None), expires_at=getattr(r, "expires_at", None),
            active=bool(getattr(r, "active", True)),
        ) for r in rows]
        return BlocklistResponse(items=items, total=len(items))

    def add(self, body: BlocklistCreate) -> BlocklistRead:
        ip = str(body.ip)
        # TODO(security): kiểm tra quyền người gọi, allowlist quản trị, IP nội bộ
        # quan trọng và chính sách chặn trước khi gửi lệnh sang firewall.
        now = datetime.now(timezone.utc)
        expires_at = None if body.duration_s == 0 else now.timestamp() + body.duration_s
        record = self.repository.create_or_update({
            "ip": ip, "scope": body.scope, "reason": body.reason,
            "duration_s": body.duration_s, "flow_id": body.flow_id,
            "created_at": now, "expires_at_epoch": expires_at, "active": True,
        })
        # Repository nên trả ORM row hoặc dict đã chuẩn hóa.
        get = lambda key, default=None: record.get(key, default) if isinstance(record, dict) else getattr(record, key, default)
        expiry = get("expires_at")
        return BlocklistRead(
            ip=str(get("ip", ip)), scope=get("scope", body.scope),
            reason=get("reason", body.reason), duration_s=int(get("duration_s", body.duration_s)),
            created_at=get("created_at", now), expires_at=expiry, active=bool(get("active", True)),
        )

    def remove(self, ip: str) -> bool:
        # TODO(integration): nếu đã áp dụng firewall thật, cần đồng bộ gỡ rule và
        # xử lý trường hợp DB thành công nhưng firewall thất bại (hoặc ngược lại).
        return self.repository.delete(ip)
