-- ---------------------------------------------------------------------------
-- Agent interface (Phase 0 — see docs/agent-migration-plan.md). A conversation
-- is a chat session; each message stores Claude's raw content blocks (not just
-- extracted text) so tool_use/tool_result blocks round-trip exactly when a
-- conversation resumes after a page reload or process restart.
-- ---------------------------------------------------------------------------
create table if not exists agent_conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text,                          -- first user message, truncated, for a history list
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table agent_conversations enable row level security;

create policy "agent_conversations_owner_all" on agent_conversations
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create table if not exists agent_messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references agent_conversations(id) on delete cascade,
  role text not null,                  -- 'user' | 'assistant' | 'tool_result'
  content jsonb not null,              -- raw Claude content blocks — replayed verbatim on resume
  created_at timestamptz not null default now()
);

alter table agent_messages enable row level security;

create policy "agent_messages_owner_all" on agent_messages
  for all using (
    auth.uid() = (select user_id from agent_conversations where agent_conversations.id = agent_messages.conversation_id)
  ) with check (
    auth.uid() = (select user_id from agent_conversations where agent_conversations.id = agent_messages.conversation_id)
  );

create index if not exists agent_messages_conversation_id_idx on agent_messages(conversation_id, created_at);
