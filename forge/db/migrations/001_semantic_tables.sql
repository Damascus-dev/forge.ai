-- Forge Semantic Logging Schema
-- Phase 6: PostgreSQL + pgvector setup
-- Created: May 24, 2026

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent Actions Table
-- Stores all agent observations, decisions, actions, and results
CREATE TABLE IF NOT EXISTS agent_actions (
  id BIGSERIAL PRIMARY KEY,
  experiment_id UUID NOT NULL,
  agent_id UUID NOT NULL,
  step_number INT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  
  -- Action content
  observation TEXT,
  reasoning TEXT,
  decision TEXT,
  action TEXT,
  result TEXT,
  
  -- Metadata
  tool_name VARCHAR(50),
  success BOOLEAN,
  error_message TEXT,
  duration_ms INT,
  
  -- Foreign keys
  embedding_id UUID,
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_agent_actions_experiment_id ON agent_actions(experiment_id);
CREATE INDEX idx_agent_actions_agent_id ON agent_actions(agent_id);
CREATE INDEX idx_agent_actions_timestamp ON agent_actions(timestamp);

-- Embeddings Table
-- Stores 768-dimensional vectors for semantic search
CREATE TABLE IF NOT EXISTS embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  action_id BIGINT NOT NULL REFERENCES agent_actions(id) ON DELETE CASCADE,
  
  -- Vector embedding (768-dim for nomic-embed-text)
  vector vector(768) NOT NULL,
  
  -- Metadata
  text_summary TEXT,
  model_name VARCHAR(100),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Vector index for fast similarity search
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat(vector vector_cosine_ops);
CREATE INDEX idx_embeddings_action_id ON embeddings(action_id);

-- Weekly Summaries Table
-- Stores auto-generated weekly recaps
CREATE TABLE IF NOT EXISTS weekly_summaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  week_start DATE NOT NULL,
  week_end DATE NOT NULL,
  
  -- Summary content
  markdown_summary TEXT,
  semantic_insights JSONB,
  
  -- Statistics
  total_actions INT,
  successful_actions INT,
  failed_actions INT,
  unique_experiments INT,
  unique_agents INT,
  
  -- Analysis
  key_themes TEXT[],
  anomalies JSONB,
  recommendations TEXT,
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Unique index on week
CREATE UNIQUE INDEX idx_weekly_summaries_week ON weekly_summaries(week_start);

-- Grant access
GRANT ALL ON agent_actions TO forge;
GRANT ALL ON embeddings TO forge;
GRANT ALL ON weekly_summaries TO forge;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO forge;

-- Comments for documentation
COMMENT ON TABLE agent_actions IS 'All agent observations, decisions, and actions';
COMMENT ON TABLE embeddings IS '768-dimensional vector embeddings for semantic search';
COMMENT ON TABLE weekly_summaries IS 'Auto-generated weekly summaries of agent work';
