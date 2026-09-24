CREATE OR REPLACE TABLE `driiiportfolio.snap_growth_transform.clean_events`
PARTITION BY event_date CLUSTER BY user_id, event_name AS
SELECT DISTINCT
  event_id, user_id, DATE(event_ts) AS event_date, event_ts,
  LOWER(TRIM(event_name)) AS event_name, session_id
FROM `driiiportfolio.snap_growth_raw.events`
WHERE event_id IS NOT NULL AND user_id IS NOT NULL
  AND event_ts IS NOT NULL
  AND event_name IN ('app_open','message_sent','story_view','lens_used','feature_discovered');
