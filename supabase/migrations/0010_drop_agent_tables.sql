-- Reverses 0009_agent.sql. The standalone chat-agent approach (a general
-- multi-tool conversational front-end for the whole pipeline) was superseded
-- by a narrower design: a conversational "campaign scoping" step embedded
-- directly in the existing wizard, not a separate agent surface. See
-- campaign_plan_items / campaigns.content_plan in 0011_campaign_scoping.sql.
drop table if exists agent_messages;
drop table if exists agent_conversations;
