-- =========================================================================
-- 1. TẠO CƠ SỞ DỮ LIỆU (Tùy chọn - Bỏ qua nếu bạn đã có sẵn DB)
-- =========================================================================
-- CREATE DATABASE network_security_db;
-- \c network_security_db;

-- =========================================================================
-- 2. TẠO CÁC BẢNG (TABLES)
-- =========================================================================

-- Bảng lưu trữ thông tin các máy chủ (IP)
CREATE TABLE hosts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ip_address INET NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bảng lưu thông tin các tập dữ liệu (Datasets)
CREATE TABLE datasets (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bảng lưu thông tin các luồng mạng (Flows)
CREATE TABLE flows (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT REFERENCES datasets(id),
    src_host_id BIGINT NOT NULL REFERENCES hosts(id),
    dst_host_id BIGINT NOT NULL REFERENCES hosts(id),

    flow_start_ms BIGINT NOT NULL,
    flow_end_ms BIGINT,
    flow_start_at TIMESTAMPTZ NOT NULL,
    flow_duration_ms BIGINT,

    protocol SMALLINT,
    src_port INTEGER CHECK (src_port BETWEEN 0 AND 65535),
    dst_port INTEGER CHECK (dst_port BETWEEN 0 AND 65535),

    label SMALLINT CHECK (label IN (0, 1)),
    attack_family TEXT,
    zero_duration BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bảng lưu trữ các snapshot dạng đồ thị mạng theo cửa sổ thời gian
CREATE TABLE graph_snapshots (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT REFERENCES datasets(id),
    session_id TEXT,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    window_minutes SMALLINT NOT NULL,
    num_nodes INTEGER,
    num_edges INTEGER,
    artifact_uri TEXT,

    CHECK (window_end > window_start),
    CHECK (window_minutes > 0)
);

-- Bảng trung gian ánh xạ quan hệ nhiều-nhiều giữa snapshot và flows
CREATE TABLE graph_snapshot_flows (
    snapshot_id BIGINT NOT NULL
        REFERENCES graph_snapshots(id) ON DELETE CASCADE,
    flow_id BIGINT NOT NULL
        REFERENCES flows(id) ON DELETE CASCADE,
    edge_index INTEGER,

    PRIMARY KEY (snapshot_id, flow_id)
);

-- Bảng quản lý phiên bản mô hình AI/ML
CREATE TABLE model_versions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    inference_mode TEXT NOT NULL
        CHECK (inference_mode IN ('mock', 'model')),
    checkpoint_uri TEXT,
    preprocessing_version TEXT,
    feature_schema_uri TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (name, version)
);

-- Bảng lưu trữ kết quả dự đoán từ mô hình
CREATE TABLE predictions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flow_id BIGINT NOT NULL REFERENCES flows(id),
    snapshot_id BIGINT REFERENCES graph_snapshots(id),
    model_version_id BIGINT NOT NULL
        REFERENCES model_versions(id),

    attack_score DOUBLE PRECISION,
    predicted_label TEXT NOT NULL,
    predicted_family TEXT,
    threshold_used DOUBLE PRECISION,
    inference_status TEXT NOT NULL DEFAULT 'completed',
    predicted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (
        attack_score IS NULL
        OR (attack_score >= 0 AND attack_score <= 1)
    )
);

-- Bảng lưu trữ các cảnh báo (Alerts) sinh ra từ kết quả dự đoán
CREATE TABLE alerts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prediction_id BIGINT NOT NULL REFERENCES predictions(id),
    severity TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'new',
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- =========================================================================
-- 3. TẠO CÁC CHỈ MỤC (INDEXES) TỐI ƯU TRUY VẤN
-- =========================================================================

CREATE INDEX idx_flows_start_at
    ON flows(flow_start_at DESC);

CREATE INDEX idx_flows_src_host
    ON flows(src_host_id);

CREATE INDEX idx_flows_dst_host
    ON flows(dst_host_id);

CREATE INDEX idx_predictions_flow_time
    ON predictions(flow_id, predicted_at DESC);

CREATE INDEX idx_alerts_status_time
    ON alerts(status, created_at DESC);