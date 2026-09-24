CREATE OR REPLACE TABLE `driiiportfolio.snap_growth_analytics.user_experiment_metrics`
CLUSTER BY treatment_group, market AS
WITH base AS (
  SELECT u.user_id, u.signup_date, u.market, u.device_type,
         u.acquisition_channel, a.treatment_group, a.assignment_ts
  FROM `driiiportfolio.snap_growth_raw.users` u
  JOIN `driiiportfolio.snap_growth_raw.experiment_assignments` a USING (user_id)
), agg AS (
  SELECT b.user_id,
    COUNTIF(e.event_name = 'app_open' AND e.event_date BETWEEN b.signup_date AND DATE_ADD(b.signup_date, INTERVAL 6 DAY)) > 0 AS activated,
    COUNTIF(e.event_date BETWEEN b.signup_date AND DATE_ADD(b.signup_date, INTERVAL 27 DAY)) > 0 AS d28_retained,
    COUNTIF(e.event_name = 'feature_discovered' AND e.event_date BETWEEN b.signup_date AND DATE_ADD(b.signup_date, INTERVAL 6 DAY)) > 0 AS discovered_feature,
    COUNTIF(e.event_name = 'message_sent' AND e.event_date BETWEEN b.signup_date AND DATE_ADD(b.signup_date, INTERVAL 27 DAY)) AS messages_28d,
    COUNTIF(e.event_name = 'app_open' AND e.event_date BETWEEN b.signup_date AND DATE_ADD(b.signup_date, INTERVAL 27 DAY)) AS opens_28d
  FROM base b LEFT JOIN `driiiportfolio.snap_growth_transform.clean_events` e USING (user_id)
  GROUP BY b.user_id
)
SELECT b.*, a.* EXCEPT(user_id),
  EXISTS(SELECT 1 FROM `driiiportfolio.snap_growth_raw.subscriptions` s
         WHERE s.user_id=b.user_id AND s.subscription_date BETWEEN b.signup_date AND DATE_ADD(b.signup_date, INTERVAL 27 DAY)) AS subscribed_28d
FROM base b JOIN agg a USING (user_id);
