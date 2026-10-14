# NetFlow Host-Graph IDS — Backend scaffold

Bộ khung backend FastAPI cho dashboard NetFlow/Host Graph IDS. Các file này phân
chia API schemas và nghiệp vụ, nhưng **chưa phải backend production hoàn chỉnh**:
repository PostgreSQL, ORM models, authentication, migrations, GNN inference và
cơ chế firewall chưa được cài đặt.

## 1. Cấu trúc

```text
app/backend/
├── main.py                     # FastAPI routes; wire service vào endpoint
├── schemas.py                  # Hợp đồng request/response
├── services/
│   ├── flow_service.py         # Truy vấn/chuẩn hóa flow
│   ├── prediction_service.py   # MockPredictor và khung GNNPredictor
│   ├── alert_service.py        # Feedback và nghiệp vụ cảnh báo
│   └── blocklist_service.py    # Quản lý blocklist
└── README.md
```

Trong gói mẫu, `schemas.py` được import như `from schemas import ...` để dễ đọc
độc lập. Khi đặt vào package `app/backend`, hãy đổi sang import package nhất quán,
ví dụ `from app.backend.schemas import ...` hoặc `from ..schemas import ...` tùy
cách chạy ứng dụng. Không trộn hai kiểu import trong cùng project.

## 2. Chạy API

Tạo môi trường và cài dependency tối thiểu:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install fastapi uvicorn pydantic
```

Khi đã có `app/backend/main.py` và đã wire dependencies, chạy từ thư mục gốc repo:

```bash
uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000
```

Mở `/docs` để xem OpenAPI. Các service trong scaffold chưa tự tạo endpoint; route
phải được khai báo trong `main.py`.

## 3. Hợp đồng tích hợp database

Không để service tự tạo connection/session. Tạo `db.py` cho SQLAlchemy engine và
session dependency, `db_models.py` cho ORM entities, và `repositories/` để thực thi
truy vấn. Repository được truyền vào service qua constructor (dependency injection).

Các repository dự kiến:

- `FlowRepository.list_flows(since, limit, offset)` và `get_flow(flow_id)`.
- `AlertRepository.get_flow(flow_id)` và `upsert_feedback(flow_id, label, note)`.
- `BlocklistRepository.list_entries()`, `get_active(ip)`, `create_or_update(data)` và `delete(ip)`.

Tên bảng/cột cần khớp schema PostgreSQL thật. Nên quản lý thay đổi schema bằng
Alembic migrations, dùng transaction, index cho timestamp/src/dst và kiểm thử truy
vấn trên dữ liệu đại diện trước khi đưa vào dashboard.

## 4. Tích hợp GNN

1. Lưu checkpoint cùng metadata versioned: tên/thứ tự features, scaler, label map,
   graph window, threshold, model architecture và version thư viện.
2. Nạp model một lần trong lifespan/startup của ứng dụng, không nạp lại mỗi request.
3. Dùng cùng pipeline preprocessing như lúc training; không fit scaler trên dữ liệu
   production/test và không thay thứ tự 91 features.
4. Với Host Graph, xác định rõ dự đoán là edge/flow classification hay node/graph
   classification; flow request có thể cần snapshot và lân cận, không chỉ vector flow.
5. Chạy inference bằng `model.eval()` và `torch.inference_mode()`. Xử lý lỗi model
   chưa sẵn sàng bằng HTTP 503; không âm thầm trả dữ liệu mock.
6. Ghi lại model version, timestamp, score, label, threshold và snapshot ID để có
   thể truy vết kết quả.

`MockPredictor` trong `prediction_service.py` cố ý trả `unknown` và `score=None`.
Đây là hành vi an toàn để kiểm thử giao diện, không tạo ra kết quả tấn công giả.
Không đưa kết quả mock vào báo cáo khoa học.

## 5. Tích hợp blocklist

`blocklist` trong DB chỉ là bản ghi quản lý. Muốn chặn thật cần adapter riêng cho
firewall/SDN, xác thực người dùng, phân quyền, allowlist, audit log, thời hạn rule,
kiểm tra kết quả thực thi và cơ chế rollback. Không tự động cách ly host chỉ dựa
trên một score của model.

## 6. Kiểm thử nên có

- Schema: IP sai, port ngoài khoảng, giá trị âm, label không hợp lệ.
- Flow service: cửa sổ thời gian, phân trang, flow không tồn tại.
- Prediction: mock trả `mode=mock`, model chưa sẵn sàng trả lỗi rõ ràng, feature
  mismatch không bị bỏ qua.
- Feedback: flow không tồn tại, ghi nhận/xóa feedback, không tự huấn luyện lại model.
- Blocklist: thêm trùng IP, hết hạn, gỡ IP không tồn tại, lỗi adapter firewall.
- API: CORS chỉ cho origin frontend đã cấu hình; authentication/rate limits trước
  khi mở mạng; không bind `0.0.0.0` trong môi trường production nếu chưa bảo vệ.

## 7. Lưu ý về frontend hiện tại

Frontend đang dùng `f.p`, `f.type`, `f.ago`, trong khi schema backend dùng các tên
chuẩn hóa `score`, `attack_family`, `timestamp`. Hãy chọn một hợp đồng duy nhất.
Có thể thêm lớp mapper ở frontend hoặc đổi response DTO, nhưng không nên dùng đồng
thời hai bộ tên trường không nhất quán. KPI live phải được tính từ response thật;
không dùng số liệu ngẫu nhiên hoặc metric validation cố định như thể đó là số liệu
production.
