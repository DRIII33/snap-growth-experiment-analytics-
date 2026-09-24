SELECT 'duplicate_event_id' AS check_name, COUNT(*) AS failures
FROM (
  SELECT event_id FROM `driiiportfolio.snap_growth_raw.events`
  GROUP BY event_id HAVING COUNT(*) > 1
)
UNION ALL
SELECT 'orphan_event_user', COUNT(*)
FROM `driiiportfolio.snap_growth_raw.events` e
LEFT JOIN `driiiportfolio.snap_growth_raw.users` u USING (user_id)
WHERE u.user_id IS NULL
UNION ALL
SELECT 'invalid_treatment', COUNT(*)
FROM `driiiportfolio.snap_growth_raw.experiment_assignments`
WHERE treatment_group NOT IN ('control', 'treatment');
