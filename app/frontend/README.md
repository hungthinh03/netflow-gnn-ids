# Frontend - IDS Dashboard

Dashboard theo dõi luồng mạng, kết quả phát hiện của mô hình GNN và xử lý cảnh báo.
Hiện là **mockup chạy bằng dữ liệu mẫu**; HTML/CSS/JS thuần, không cần bước build.

## Nối với backend

Trong `js/api.js`, đặt `API.base = 'http://127.0.0.1:8000'`. Các thao tác ghi đã gọi:

| Thao tác | Endpoint |
|---|---|
| Chặn IP / cách ly host | `POST /api/blocklist` với `{ip, scope, target_role, reason, duration_s, flow_id}` |
| Bỏ chặn | `DELETE /api/blocklist/{ip}` |
| Đánh dấu cảnh báo sai | `POST /api/flows/{id}/feedback` với `{label}` |

Việc **đọc** dữ liệu chưa gọi API: danh sách flow đang lấy từ `js/data.js`.
Khi có backend cần thay bằng `GET /api/flows?window=30m`, trả về mỗi flow gồm
`id, ago (giây), src, dst, proto, port, bytes, pkts, dur, ttl, flags, retrans, iat, p (điểm tấn công), type`.
Biểu đồ và các chỉ số trên cùng hiện cũng là số giả lập (hàm `buckets()` trong `app.js`),
cần được thay bằng số liệu tổng hợp từ backend.

Ngưỡng cảnh báo (`state.thr` trong `app.js`) là giá trị cố định, nên lấy từ metadata của mô hình.
