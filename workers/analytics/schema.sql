-- Schema para D1 database de analytics

CREATE TABLE IF NOT EXISTS analytics_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL, -- session_start, mission_start, scene_view, choice_made, etc.
    agent_id TEXT,
    scene_id TEXT,
    choice_text TEXT,
    target_scene TEXT,
    puzzle_id TEXT,
    ending_id TEXT,
    timestamp INTEGER NOT NULL,
    user_agent TEXT,
    referrer TEXT,
    metadata TEXT, -- JSON string con datos adicionales
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar performance
CREATE INDEX IF NOT EXISTS idx_session_id ON analytics_events(session_id);
CREATE INDEX IF NOT EXISTS idx_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_agent_id ON analytics_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_scene_id ON analytics_events(scene_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON analytics_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_ending_id ON analytics_events(ending_id);
