-- Local AI Tutor MVP — SQLite schema for memory
-- Run via: sqlite3 data/tutor.db < backend/schemas/schema.sql

-- Conversation history (single-user MVP)
CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at);

-- Topic strength (weak/strong) for spaced repetition / personalization
CREATE TABLE IF NOT EXISTS topics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  strength TEXT NOT NULL CHECK (strength IN ('weak', 'medium', 'strong')),
  concept_summary TEXT,
  last_touched_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_topics_name ON topics(name);

-- Teaching turns: explain / question / correction (for Teaching Engine state)
CREATE TABLE IF NOT EXISTS teaching_turns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  turn_type TEXT NOT NULL CHECK (turn_type IN ('explain', 'question', 'correction', 'feedback')),
  concept TEXT,
  user_answer TEXT,
  is_correct INTEGER,  -- 0/1
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_teaching_turns_session ON teaching_turns(session_id);
