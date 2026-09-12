-- Non-fatal notices about a campaign's generation, distinct from `error_message`
-- (which means the pipeline actually failed a step). First use: the reference-image
-- cap (brand + product combined, capped at OpenAI's 16-image edit limit in
-- step2_variants.py) silently truncated some product photos — previously only a
-- server-side log line, now visible to the user instead of silently dropped.
alter table campaigns add column if not exists warning_message text;
