"""Điểm tích hợp duy nhất giữa API và predictor mock/GNN thật.

Đừng nạp checkpoint hoặc dựng graph trong endpoint FastAPI. Đóng gói quy trình đó
ở adapter predictor để có thể kiểm thử độc lập và thay model mà không sửa API.
"""
from typing import Protocol, Any
from schemas import FlowFeatures, PredictionRequest, PredictionResult, PredictionMode


class Predictor(Protocol):
    mode: PredictionMode
    model_name: str | None
    model_version: str | None

    def predict(self, request: PredictionRequest) -> PredictionResult: ...


class MockPredictor:
    """Predictor giả lập cho phát triển UI; kết quả KHÔNG phải kết quả nghiên cứu.

    Dùng score cố định/heuristic rõ ràng để test luồng API. Không dùng các kết quả
    này trong báo cáo thực nghiệm và luôn trả mode='mock'.
    """
    mode: PredictionMode = "mock"
    model_name = "mock_predictor"
    model_version = None

    def predict(self, request: PredictionRequest) -> PredictionResult:
        # Placeholder có chủ ý: không giả vờ đã chạy GNN.
        return PredictionResult(
            label="unknown", score=None, attack_family=None, threshold=None,
            mode="mock", model_name=self.model_name,
            explanation="Mock mode: chưa có suy luận từ mô hình đã huấn luyện.",
        )


class GNNPredictor:
    """Khung tích hợp model thật. Chưa thể dự đoán đến khi hoàn thiện TODO.

    TODO(model):
    1. Nạp checkpoint cùng metadata (feature names/order, scaler, label mapping,
       graph window, threshold và model version) một lần khi ứng dụng khởi động.
    2. Validate và biến đổi đúng feature schema đã dùng khi train.
    3. Truy vấn/build Host Graph Snapshot phù hợp với timestamp/flow.
    4. Chạy model.eval() trong torch.inference_mode(); không fit scaler ở inference.
    5. Ánh xạ logits sang score/label theo đúng bài toán (edge classification hay
       graph/node classification); ghi rõ nếu score chưa được calibration.
    6. Trả lỗi ModelNotReady nếu checkpoint/config không tồn tại, không fallback
       im lặng sang kết quả giả lập.
    """
    mode: PredictionMode = "model"
    model_name = "hostgraph-gnn"
    model_version: str | None = None

    def __init__(self, checkpoint_path: str, config_path: str):
        self.checkpoint_path = checkpoint_path
        self.config_path = config_path
        self.ready = False
        # TODO: load checkpoint, feature pipeline, label map và graph builder.
        # Khi load thành công, set self.ready = True.

    def predict(self, request: PredictionRequest) -> PredictionResult:
        if not self.ready:
            raise RuntimeError("GNN chưa sẵn sàng: checkpoint/pipeline chưa được tích hợp.")
        # TODO: tạo graph/context và chạy inference thật.
        raise NotImplementedError("Implement GNN inference sau khi checkpoint và schema ổn định.")


class PredictionService:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def predict(self, request: PredictionRequest) -> PredictionResult:
        # Nơi phù hợp để bổ sung logging, timing, validation phiên bản feature và
        # lưu kết quả dự đoán qua PredictionRepository khi database đã sẵn sàng.
        return self.predictor.predict(request)

    def status(self) -> dict[str, Any]:
        ready = getattr(self.predictor, "ready", self.predictor.mode == "mock")
        return {
            "mode": self.predictor.mode,
            "ready": bool(ready),
            "model_name": self.predictor.model_name,
            "model_version": self.predictor.model_version,
            "message": "Mock predictor; không phải kết quả GNN thật." if self.predictor.mode == "mock" else (
                "Model ready" if ready else "GNN checkpoint/pipeline chưa sẵn sàng"
            ),
        }
