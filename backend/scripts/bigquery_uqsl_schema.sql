-- UQSL Quality Feedback Analytics Schema (BigQuery)
-- Version: 1.0
-- Generated: 2026-01-16
--
-- This schema supports the Universal Quality Selection Layer (UQSL)
-- analytics for quality improvement tracking and Thompson Sampling optimization.
--
-- Usage:
--   bq query --use_legacy_sql=false < bigquery_uqsl_schema.sql

-- Create dataset if not exists
CREATE SCHEMA IF NOT EXISTS vivid_analytics
OPTIONS (
  description = 'Vivid UQSL Analytics Dataset',
  location = 'asia-northeast3'
);

-- ============================================================================
-- 1. UQSL Quality Feedback Table
-- Main event table for quality selection tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS vivid_analytics.uqsl_quality_feedback (
    -- Identifiers
    event_id STRING NOT NULL,
    app_key STRING NOT NULL,
    prompt_hash STRING NOT NULL,
    user_id STRING,

    -- Generation metadata
    n_candidates INT64,
    generation_latency_ms INT64,

    -- Candidate quality scores (array of structs)
    candidate_scores ARRAY<STRUCT<
        idx INT64,
        groundedness FLOAT64,
        relevance FLOAT64,
        coherence FLOAT64,
        creativity FLOAT64,
        safety FLOAT64,
        total_score FLOAT64,
        backend_used STRING,
        latency_ms INT64
    >>,

    -- Selection info
    selected_idx INT64,
    selection_method STRING,  -- auto, hitl, hybrid, llm_judge
    selection_latency_ms INT64,
    auto_threshold FLOAT64,

    -- User feedback
    user_feedback STRING,  -- positive, negative, null
    feedback_latency_ms INT64,
    feedback_comment STRING,

    -- Thompson Sampling arms
    arms_used ARRAY<STRING>,
    arm_rewards ARRAY<STRUCT<
        arm_id STRING,
        reward BOOL
    >>,

    -- Context
    user_tier STRING,  -- free, premium, dev
    dimension STRING,
    auteur_key STRING,

    -- Ensemble++ metadata
    ensemble_enabled BOOL,
    ensemble_recommended STRING,  -- a, b, ab

    -- Timestamps
    event_timestamp TIMESTAMP NOT NULL,
    generation_started_at TIMESTAMP,
    selection_completed_at TIMESTAMP,
    feedback_submitted_at TIMESTAMP
)
PARTITION BY DATE(event_timestamp)
CLUSTER BY app_key, selection_method, user_tier
OPTIONS (
    description = 'UQSL quality feedback events for Thompson Sampling optimization'
);


-- ============================================================================
-- 2. Quality Metrics Aggregated View
-- Daily aggregation for monitoring and dashboards
-- ============================================================================

CREATE OR REPLACE VIEW vivid_analytics.uqsl_quality_metrics AS
SELECT
    app_key,
    selection_method,
    user_tier,
    DATE(event_timestamp) AS date,

    -- Volume metrics
    COUNT(*) AS total_selections,
    COUNT(DISTINCT prompt_hash) AS unique_prompts,
    COUNT(user_feedback) AS feedback_count,

    -- Quality metrics
    AVG(IF(user_feedback = 'positive', 1, 0)) AS positive_rate,
    AVG(candidate_scores[SAFE_OFFSET(0)].total_score) AS avg_top_score,
    AVG(candidate_scores[SAFE_OFFSET(selected_idx)].total_score) AS avg_selected_score,

    -- Quality dimension breakdown
    AVG(candidate_scores[SAFE_OFFSET(selected_idx)].groundedness) AS avg_groundedness,
    AVG(candidate_scores[SAFE_OFFSET(selected_idx)].relevance) AS avg_relevance,
    AVG(candidate_scores[SAFE_OFFSET(selected_idx)].coherence) AS avg_coherence,
    AVG(candidate_scores[SAFE_OFFSET(selected_idx)].creativity) AS avg_creativity,
    AVG(candidate_scores[SAFE_OFFSET(selected_idx)].safety) AS avg_safety,

    -- Latency metrics
    APPROX_QUANTILES(generation_latency_ms, 100)[OFFSET(50)] AS p50_generation_latency,
    APPROX_QUANTILES(generation_latency_ms, 100)[OFFSET(95)] AS p95_generation_latency,
    APPROX_QUANTILES(selection_latency_ms, 100)[OFFSET(50)] AS p50_selection_latency,
    APPROX_QUANTILES(feedback_latency_ms, 100)[OFFSET(50)] AS p50_feedback_latency,

    -- Auto-selection rate (for hybrid strategy)
    COUNTIF(selection_method = 'auto') / COUNT(*) AS auto_selection_rate

FROM vivid_analytics.uqsl_quality_feedback
WHERE event_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY app_key, selection_method, user_tier, date;


-- ============================================================================
-- 3. Thompson Sampling Arm Performance View
-- Track arm success rates over time
-- ============================================================================

CREATE OR REPLACE VIEW vivid_analytics.uqsl_arm_performance AS
SELECT
    arm.arm_id,
    DATE(event_timestamp) AS date,

    -- Trial metrics
    COUNT(*) AS total_trials,
    COUNTIF(arm.reward) AS successful_trials,
    AVG(IF(arm.reward, 1.0, 0.0)) AS success_rate,

    -- Confidence (more trials = more confidence)
    1 - (1.0 / (COUNT(*) + 1)) AS confidence,

    -- Context
    app_key,
    selection_method

FROM vivid_analytics.uqsl_quality_feedback,
UNNEST(arm_rewards) AS arm
WHERE event_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY arm.arm_id, date, app_key, selection_method;


-- ============================================================================
-- 4. Ensemble++ Comparison View
-- Track 3-way comparison results (NeurIPS 2025)
-- ============================================================================

CREATE OR REPLACE VIEW vivid_analytics.uqsl_ensemble_comparison AS
SELECT
    app_key,
    DATE(event_timestamp) AS date,

    -- Selection distribution
    COUNTIF(ensemble_recommended = 'a') AS backend_a_wins,
    COUNTIF(ensemble_recommended = 'b') AS backend_b_wins,
    COUNTIF(ensemble_recommended = 'ab') AS ensemble_wins,

    -- Win rates
    COUNTIF(ensemble_recommended = 'a') / COUNT(*) AS backend_a_win_rate,
    COUNTIF(ensemble_recommended = 'b') / COUNT(*) AS backend_b_win_rate,
    COUNTIF(ensemble_recommended = 'ab') / COUNT(*) AS ensemble_win_rate,

    -- User agreement (did user select what was recommended?)
    AVG(IF(
        (ensemble_recommended = 'a' AND selected_idx = 0) OR
        (ensemble_recommended = 'b' AND selected_idx = 1) OR
        (ensemble_recommended = 'ab' AND selected_idx = 2),
        1.0, 0.0
    )) AS user_agreement_rate,

    COUNT(*) AS total_comparisons

FROM vivid_analytics.uqsl_quality_feedback
WHERE ensemble_enabled = TRUE
  AND event_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY app_key, date;


-- ============================================================================
-- 5. Quality Trend Analysis View
-- Week-over-week quality improvement tracking
-- ============================================================================

CREATE OR REPLACE VIEW vivid_analytics.uqsl_quality_trend AS
WITH weekly_metrics AS (
    SELECT
        app_key,
        DATE_TRUNC(DATE(event_timestamp), WEEK) AS week_start,
        AVG(IF(user_feedback = 'positive', 1.0, 0.0)) AS positive_rate,
        AVG(candidate_scores[SAFE_OFFSET(selected_idx)].total_score) AS avg_quality_score,
        COUNT(*) AS total_selections
    FROM vivid_analytics.uqsl_quality_feedback
    WHERE event_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
    GROUP BY app_key, week_start
),
with_prev AS (
    SELECT
        *,
        LAG(positive_rate) OVER (PARTITION BY app_key ORDER BY week_start) AS prev_positive_rate,
        LAG(avg_quality_score) OVER (PARTITION BY app_key ORDER BY week_start) AS prev_quality_score
    FROM weekly_metrics
)
SELECT
    app_key,
    week_start,
    positive_rate,
    avg_quality_score,
    total_selections,
    positive_rate - prev_positive_rate AS positive_rate_change,
    avg_quality_score - prev_quality_score AS quality_score_change,
    SAFE_DIVIDE(positive_rate - prev_positive_rate, prev_positive_rate) AS positive_rate_pct_change
FROM with_prev
ORDER BY app_key, week_start DESC;


-- ============================================================================
-- 6. Hallucination Detection View
-- Track groundedness scores to detect potential hallucinations
-- ============================================================================

CREATE OR REPLACE VIEW vivid_analytics.uqsl_hallucination_risk AS
SELECT
    app_key,
    DATE(event_timestamp) AS date,

    -- Low groundedness = high hallucination risk
    COUNTIF(candidate_scores[SAFE_OFFSET(selected_idx)].groundedness < 0.5) AS low_groundedness_count,
    COUNT(*) AS total_count,
    COUNTIF(candidate_scores[SAFE_OFFSET(selected_idx)].groundedness < 0.5) / COUNT(*) AS hallucination_risk_rate,

    -- Average groundedness
    AVG(candidate_scores[SAFE_OFFSET(selected_idx)].groundedness) AS avg_groundedness,

    -- Groundedness by user feedback
    AVG(IF(user_feedback = 'negative', candidate_scores[SAFE_OFFSET(selected_idx)].groundedness, NULL)) AS avg_groundedness_negative_feedback,
    AVG(IF(user_feedback = 'positive', candidate_scores[SAFE_OFFSET(selected_idx)].groundedness, NULL)) AS avg_groundedness_positive_feedback

FROM vivid_analytics.uqsl_quality_feedback
WHERE event_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY app_key, date;


-- ============================================================================
-- 7. Cost Analysis View
-- Track LLM costs by tier and method
-- ============================================================================

CREATE OR REPLACE VIEW vivid_analytics.uqsl_cost_analysis AS
SELECT
    user_tier,
    selection_method,
    DATE(event_timestamp) AS date,

    -- Volume
    COUNT(*) AS total_requests,
    SUM(n_candidates) AS total_candidates_generated,

    -- Estimated costs (example rates, adjust as needed)
    -- Free tier: ~$0 (rule-based)
    -- Premium tier: ~$0.001 per LLM judge call
    -- Dev tier: ~$0.002 per full analytics
    SUM(CASE
        WHEN user_tier = 'free' THEN 0.0
        WHEN user_tier = 'premium' THEN n_candidates * 0.001
        WHEN user_tier = 'dev' THEN n_candidates * 0.002
        ELSE 0.0
    END) AS estimated_cost_usd,

    -- Cost efficiency
    SUM(CASE
        WHEN user_tier = 'free' THEN 0.0
        WHEN user_tier = 'premium' THEN n_candidates * 0.001
        WHEN user_tier = 'dev' THEN n_candidates * 0.002
        ELSE 0.0
    END) / COUNT(*) AS avg_cost_per_request

FROM vivid_analytics.uqsl_quality_feedback
WHERE event_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY user_tier, selection_method, date;


-- ============================================================================
-- Sample Queries
-- ============================================================================

-- 1. Get top performing apps by positive feedback rate
/*
SELECT app_key, positive_rate, total_selections
FROM vivid_analytics.uqsl_quality_metrics
WHERE date = CURRENT_DATE() - 1
ORDER BY positive_rate DESC
LIMIT 10;
*/

-- 2. Get Thompson Sampling arm performance
/*
SELECT arm_id, success_rate, total_trials, confidence
FROM vivid_analytics.uqsl_arm_performance
WHERE date = CURRENT_DATE() - 1
ORDER BY success_rate DESC;
*/

-- 3. Identify apps with high hallucination risk
/*
SELECT app_key, hallucination_risk_rate, avg_groundedness
FROM vivid_analytics.uqsl_hallucination_risk
WHERE date = CURRENT_DATE() - 1
  AND hallucination_risk_rate > 0.2
ORDER BY hallucination_risk_rate DESC;
*/

-- 4. Weekly quality trend
/*
SELECT app_key, week_start, positive_rate, positive_rate_pct_change
FROM vivid_analytics.uqsl_quality_trend
WHERE app_key = 'dimension.aesthetic.direct'
ORDER BY week_start DESC
LIMIT 8;
*/
