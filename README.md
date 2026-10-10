# NetFlow GNN IDS

Hệ thống phát hiện xâm nhập mạng (IDS) dựa trên đặc trưng NetFlow, biểu diễn mạng dưới dạng Host Graph và sử dụng Graph Neural Networks (GNN) để phân loại lưu lượng tấn công.

## Features

- **Data pipeline:** tiền xử lý NetFlow, quản lý nhãn và chia tập dữ liệu.
- **Graph construction:** biểu diễn Host thành node, luồng mạng thành edge và xây dựng Graph Snapshot theo cửa sổ thời gian.
- **Model training:** baseline phi đồ thị (Random Forest, XGBoost, MLP), mô hình GNN và mô hình đề xuất.
- **Evaluation:** PR-AUC, Precision, Recall, F1-score, False Positive Rate (FPR) và feature ablation.
- **IDS dashboard:** giao diện theo dõi lưu lượng, kết quả dự đoán và cảnh báo.

## Dataset

**Nguồn tham khảo:** [Machine Learning-Based NIDS Datasets — University of Queensland](https://staff.itee.uq.edu.au/marius/NIDS_datasets/)

Dự án tham chiếu các bộ dữ liệu NetFlow phục vụ nghiên cứu NIDS, bao gồm các phiên bản chuyển đổi từ UNSW-NB15. Trang nguồn cung cấp nhiều phiên bản và định dạng dữ liệu; cần xác định chính xác phiên bản được sử dụng trong từng thí nghiệm.

| Phiên bản tham khảo | Đặc điểm |
|---|---|
| NF-UNSW-NB15-v3 | 53 đặc trưng NetFlow, bao gồm đặc trưng thời gian |

Tài liệu liên quan:

- [Trang dataset gốc và liên kết tải dữ liệu](https://staff.itee.uq.edu.au/marius/NIDS_datasets/)
- [Bài báo về NetFlow v3](https://arxiv.org/abs/2503.04404)
- [Bài báo về bộ đặc trưng NetFlow chuẩn hóa](https://doi.org/10.1007/s11036-021-01843-0)

> Khi sử dụng dữ liệu, hãy trích dẫn đúng phiên bản dataset và công trình tương ứng theo hướng dẫn tại [UQ NIDS Datasets](https://staff.itee.uq.edu.au/marius/NIDS_datasets/).

### Dataset trong pipeline

Pipeline thực nghiệm hiện sử dụng các nhóm đặc trưng như thời lượng, khối lượng lưu lượng, TTL, kích thước gói tin, truyền lại, cờ TCP, dịch vụ và IAT; tổng cộng 91 đặc trưng theo cấu hình hiện tại.

**Lưu ý:** 91 đặc trưng là schema đầu vào của pipeline thực nghiệm, không mặc định là số đặc trưng gốc của các phiên bản NetFlow được công bố tại nguồn trên. Cần ghi nhận phiên bản dữ liệu, các bước biến đổi và danh sách cột thực tế để bảo đảm khả năng tái lập.

Dataset gốc không được lưu trực tiếp trong Git repository. Tải dữ liệu từ nguồn được phép sử dụng và đặt vào thư mục `data/raw/`.

Cấu trúc dữ liệu dự kiến:

```text
data/
├── raw/          # Dataset gốc, không commit
├── processed/    # Dữ liệu đã tiền xử lý, không commit mặc định
└── schema/       # Feature dictionary, schema và metadata
```

## Requirements

- Python 3.11 (phiên bản khuyến nghị; cần xác nhận tương thích với dependency thực tế).
- pip và venv.
- PyTorch và PyTorch Geometric cho các mô hình GNN.
- XGBoost, scikit-learn, pandas và NumPy cho xử lý dữ liệu và baseline.
- Node.js cho dashboard JavaScript.

Phiên bản Python, PyTorch, PyTorch Geometric, CUDA và các thư viện khác cần được khóa trong file dependency của dự án để bảo đảm môi trường tái lập.

## Setup

### 1. Clone repository

```bash
git clone <REPOSITORY_URL>
cd netflow-hostgraph-ids
```

### 2. Tạo môi trường Python sạch

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Windows PowerShell**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu sử dụng GPU, cài đặt PyTorch theo hướng dẫn tương ứng với phiên bản CUDA và môi trường tại [PyTorch — Get Started](https://pytorch.org/get-started/locally/).

## Run demo

Demo dự kiến hỗ trợ hai chế độ: suy luận trên dữ liệu flow mẫu và suy luận trên Graph Snapshot đã tạo sẵn.

### 1. Chuẩn bị dữ liệu

Tải dataset theo hướng dẫn tại mục Dataset, sau đó đặt các file đầu vào vào `data/raw/`.

```text
data/raw/
└── <dataset-file>.csv
```

Chạy bước tiền xử lý:

```bash
python scripts/prepare_data.py \
  --input data/raw/<dataset-file>.csv \
  --output data/processed/
```

### 2. Chạy suy luận

Sau khi có dữ liệu đã tiền xử lý và checkpoint mô hình:

```bash
python scripts/run_demo.py \
  --config configs/demo.yaml
```

Đường dẫn checkpoint và cấu hình đặc trưng phải khớp với mô hình đã huấn luyện. Không sử dụng lại bộ chuẩn hóa hoặc feature mapping khác với cấu hình trong quá trình training.

### 3. Khởi chạy dashboard

Nếu frontend và backend được triển khai riêng, chạy theo hướng dẫn trong `app/backend/README.md` và `app/frontend/README.md`.

Ví dụ, với backend Python:

```bash
uvicorn app.backend.main:app --host 127.0.0.1 --port 8000
```

Với frontend Node.js:

```bash
cd app/frontend
npm install
npm run dev
```

Các lệnh trên là entrypoint dự kiến; cần đồng bộ với cấu trúc module và framework thực tế của dự án trước khi phát hành bản demo.

## Repository structure

```text
.
├── app/              # Backend API và frontend dashboard
├── configs/          # Cấu hình data, graph và model
├── data/             # Schema, dữ liệu raw và processed
├── models/           # Checkpoint và model artifacts
├── notebooks/        # Notebook khám phá dữ liệu và thực nghiệm
├── results/          # Metrics, bảng kết quả và biểu đồ
├── scripts/          # Entry points cho preprocessing và demo
├── src/              # Data pipeline, graph builder, models, inference
├── requirements.txt
└── README.md
```

## Experimental protocol

- Giữ nguyên quy tắc chia train/validation/test giữa các cấu hình so sánh.
- Fit preprocessing và feature selection trên tập train; không sử dụng thông tin từ test để lựa chọn mô hình.
- Sử dụng validation để lựa chọn siêu tham số và ngưỡng phân loại.
- Đánh giá cuối cùng trên test độc lập.
- Kiểm tra trùng lặp giữa các tập và nguy cơ rò rỉ thông tin qua thời gian, Host hoặc flow.
- Báo cáo PR-AUC, Precision, Recall, F1-score và FPR; bổ sung độ trễ suy luận khi đánh giá chế độ gần thời gian thực.

## Security and data handling

- Không commit dataset chưa được phép phân phối, thông tin xác thực, file `.env`, log chứa dữ liệu nhạy cảm hoặc packet capture không được phép chia sẻ.
- Đặt các cấu hình riêng trong `.env`; chỉ commit `.env.example`.
- Chỉ kiểm thử lưu lượng tấn công trong môi trường được phép và có kiểm soát.
