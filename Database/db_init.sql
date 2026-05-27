-- =========================
-- Search and Rescue Database
-- =========================

-- Optional: create database manually first
-- CREATE DATABASE search_rescue_db;
-- \c search_rescue_db;


-- =========================
-- 1. Detection Classes
-- =========================

CREATE TABLE detection_class (
    class_id SERIAL PRIMARY KEY,
    class_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);


-- =========================
-- 2. Detections
-- =========================

CREATE TABLE detection (
    detection_id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL,
    people_count INTEGER NOT NULL DEFAULT 1,
    detection_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confidence NUMERIC(5, 2) NOT NULL,

    CONSTRAINT fk_detection_class
        FOREIGN KEY (class_id)
        REFERENCES detection_class(class_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_people_count
        CHECK (people_count >= 0),

    CONSTRAINT chk_confidence
        CHECK (confidence >= 0 AND confidence <= 100)
);


-- =========================
-- 3. Sensors
-- =========================

CREATE TABLE sensor (
    sensor_id SERIAL PRIMARY KEY,
    sensor_name VARCHAR(100) NOT NULL UNIQUE,
    unit VARCHAR(50),
    min_value NUMERIC(10, 2),
    max_value NUMERIC(10, 2),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    danger_level VARCHAR(50)
);


-- =========================
-- 4. Sensor Readings
-- =========================

CREATE TABLE sensor_reading (
    reading_id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL,
    reading_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    value NUMERIC(10, 2) NOT NULL,
    message TEXT,
    is_dangerous BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_sensor_reading_sensor
        FOREIGN KEY (sensor_id)
        REFERENCES sensor(sensor_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- =========================
-- 5. System Status
-- =========================

CREATE TABLE system_status (
    status_id SERIAL PRIMARY KEY,
    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ai_status VARCHAR(100) NOT NULL,
    front_camera_status VARCHAR(100) NOT NULL,
    detection_camera_status VARCHAR(100) NOT NULL,
    processing_status VARCHAR(100) NOT NULL
);


-- =========================
-- 6. Event Log
-- =========================

CREATE TABLE event_log (
    event_id SERIAL PRIMARY KEY,
    detection_id INTEGER,
    status_id INTEGER,
    reading_id INTEGER,
    event_type VARCHAR(100) NOT NULL,
    event_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    importance_level VARCHAR(50) NOT NULL,
    message TEXT,

    CONSTRAINT fk_event_detection
        FOREIGN KEY (detection_id)
        REFERENCES detection(detection_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_event_status
        FOREIGN KEY (status_id)
        REFERENCES system_status(status_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_event_reading
        FOREIGN KEY (reading_id)
        REFERENCES sensor_reading(reading_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);


-- =========================
-- Useful indexes
-- =========================

CREATE INDEX idx_detection_time
ON detection(detection_time);

CREATE INDEX idx_sensor_reading_time
ON sensor_reading(reading_time);

CREATE INDEX idx_event_time
ON event_log(event_time);

CREATE INDEX idx_event_importance
ON event_log(importance_level);

CREATE INDEX idx_event_detection_id
ON event_log(detection_id);

CREATE INDEX idx_event_reading_id
ON event_log(reading_id);

CREATE INDEX idx_event_status_id
ON event_log(status_id);