from pathlib import Path
import numpy as np
import pandas as pd

SEED = 20260922
N_USERS = 50_000
START = pd.Timestamp("2026-01-01", tz="UTC")
OUT = Path("data/synthetic")
rng = np.random.default_rng(SEED)
OUT.mkdir(parents=True, exist_ok=True)

markets = np.array(["north_america", "europe", "rest_of_world"])
devices = np.array(["ios", "android", "web"])
channels = np.array(["organic", "paid_social", "referral", "search"])
users = pd.DataFrame({
    "user_id": [f"u_{i:07d}" for i in range(N_USERS)],
    "signup_date": (START + pd.to_timedelta(rng.integers(0, 60, N_USERS), unit="D")).date,
    "market": rng.choice(markets, N_USERS, p=[.35, .30, .35]),
    "device_type": rng.choice(devices, N_USERS, p=[.48, .48, .04]),
    "acquisition_channel": rng.choice(channels, N_USERS, p=[.55, .20, .15, .10]),
    "latent_propensity": np.clip(rng.normal(0, 1, N_USERS), -3, 3)
})

assign = pd.DataFrame({
    "user_id": users.user_id,
    "treatment_group": rng.choice(["control", "treatment"], N_USERS),
    "assignment_ts": pd.to_datetime(users.signup_date, utc=True) + pd.to_timedelta(rng.integers(0, 86_400, N_USERS), unit="s")
})

# SIMULATED DATA-GENERATING ASSUMPTION: treatment modestly increases activation.
base_activation = 1 / (1 + np.exp(-(0.2 + .55 * users.latent_propensity)))
treatment_lift = np.where(assign.treatment_group.eq("treatment"), 0.08, 0.0)
activated = rng.random(N_USERS) < np.clip(base_activation + treatment_lift, .01, .99)

n_events = int(N_USERS * 28)
user_idx = rng.integers(0, N_USERS, n_events)
events = pd.DataFrame({
    "event_id": [f"e_{i:09d}" for i in range(n_events)],
    "user_id": users.user_id.to_numpy()[user_idx],
    "event_ts": START + pd.to_timedelta(rng.integers(0, 90 * 86_400, n_events), unit="s"),
    "event_name": rng.choice(["app_open", "message_sent", "story_view", "lens_used", "feature_discovered"], n_events, p=[.40, .18, .22, .12, .08]),
    "session_id": [f"s_{i:010d}" for i in range(n_events)]
})

# Ensure activated users have at least one discovery event; this is simulated product logic.
activated_ids = users.loc[activated, "user_id"].to_numpy()
extra = pd.DataFrame({
    "event_id": [f"e_extra_{i:08d}" for i in range(len(activated_ids))],
    "user_id": activated_ids,
    "event_ts": START + pd.to_timedelta(rng.integers(0, 7 * 86_400, len(activated_ids)), unit="s"),
    "event_name": "feature_discovered",
    "session_id": [f"s_extra_{i:08d}" for i in range(len(activated_ids))]
})
events = pd.concat([events, extra], ignore_index=True)

# Retention is simulated from activation and latent propensity, not calculated from post-treatment events.
user_frame = users.merge(assign, on="user_id")
retention_p = 1 / (1 + np.exp(-(-1.0 + .9 * user_frame.latent_propensity + .9 * activated + .10 * user_frame.treatment_group.eq("treatment"))))
retained = rng.random(N_USERS) < retention_p
subscription_p = 1 / (1 + np.exp(-(-3.2 + .5 * user_frame.latent_propensity + .25 * activated + .08 * user_frame.treatment_group.eq("treatment"))))
subscriber = rng.random(N_USERS) < subscription_p
subscriptions = user_frame.loc[subscriber, ["user_id"]].copy()
subscriptions["subscription_date"] = pd.to_datetime(user_frame.loc[subscriber, "signup_date"], utc=True) + pd.to_timedelta(rng.integers(1, 29, len(subscriptions)), unit="D")
subscriptions["plan"] = rng.choice(["plus", "lens_plus"], len(subscriptions), p=[.75, .25])

# Persist latent labels only for validation/reproducibility; exclude from analytical features.
users["simulated_activation_label"] = activated
users["simulated_d28_retained_label"] = retained

for name, frame in [("users", users), ("experiment_assignments", assign), ("events", events), ("subscriptions", subscriptions)]:
    frame.to_csv(OUT / f"{name}.csv", index=False)

assert users.user_id.is_unique
assert assign.user_id.is_unique
assert events.event_id.is_unique
assert set(assign.user_id).issubset(set(users.user_id))
assert set(events.user_id).issubset(set(users.user_id))
assert set(subscriptions.user_id).issubset(set(users.user_id))
assert set(assign.treatment_group).issubset({"control", "treatment"})
assert events.event_ts.notna().all()
print({"users": len(users), "assignments": len(assign), "events": len(events), "subscriptions": len(subscriptions)})
print(users.isna().sum())
