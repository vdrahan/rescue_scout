BEGIN;

CREATE TABLE IF NOT EXISTS schema_migration (
    version VARCHAR(100) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO detection_class (class_name, description) VALUES
    ('standing_person', 'Person standing upright (low priority)'),
    ('sitting_person', 'Person sitting (medium priority)'),
    ('crawling_person', 'Person crawling (high priority)'),
    ('lying_person', 'Person lying down (high priority)'),
    ('partially_visible_person', 'Person partially hidden/occluded (medium priority)')
ON CONFLICT (class_name) DO NOTHING;

INSERT INTO sensor (sensor_name, unit, min_value, max_value, description, danger_level) VALUES
    ('gas', 'ppm', 0, 1000, 'MQ-2 gas sensor via ADS1115 ADC', 'CRITICAL'),
    ('temperature', 'C', -10, 60, 'DHT11 temperature', 'WARNING'),
    ('humidity', '%', 0, 100, 'DHT11 relative humidity', 'INFO')
ON CONFLICT (sensor_name) DO NOTHING;

INSERT INTO schema_migration (version)
VALUES ('001_reference_data')
ON CONFLICT (version) DO NOTHING;

COMMIT;
