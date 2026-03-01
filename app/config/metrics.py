from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "workflow_api_requests_total",
    "Total API requests",
    ["path", "method", "status"],
)

REQUEST_LATENCY = Histogram(
    "workflow_api_request_latency_seconds",
    "Request latency by endpoint",
    ["path", "method"],
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 30),
)

STAGE_LATENCY = Histogram(
    "workflow_api_stage_latency_seconds",
    "Latency for orchestration stages",
    ["stage"],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10),
)

EXTERNAL_ERRORS = Counter(
    "workflow_api_external_errors_total",
    "External dependency errors",
    ["dependency"],
)

CACHE_LOOKUPS = Counter(
    "workflow_api_cache_lookups_total",
    "Total cache lookups",
    ["layer"],
)

CACHE_HITS = Counter(
    "workflow_api_cache_hits_total",
    "Total cache hits",
    ["layer"],
)

VERIFICATION_TOTAL = Counter(
    "workflow_api_verification_total",
    "Total verification attempts",
)

VERIFICATION_FAILURES = Counter(
    "workflow_api_verification_failures_total",
    "Total verification failures",
)

CORRECTION_TOTAL = Counter(
    "workflow_api_correction_total",
    "Total self-correction attempts",
)

CORRECTION_SUCCESS = Counter(
    "workflow_api_correction_success_total",
    "Total successful self-corrections",
)

AVG_REASONING_TIME = Histogram(
    "workflow_api_avg_reasoning_time_seconds",
    "Reasoning stage duration",
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 4, 8),
)

AVG_VERIFICATION_TIME = Histogram(
    "workflow_api_avg_verification_time_seconds",
    "Verification stage duration",
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1, 2),
)

CACHE_HIT_RATE = Gauge(
    "workflow_api_cache_hit_rate",
    "Cache hit ratio across all cache layers",
)

VERIFICATION_FAIL_RATE = Gauge(
    "workflow_api_verification_fail_rate",
    "Verification failure ratio",
)

CORRECTION_RATE = Gauge(
    "workflow_api_correction_rate",
    "Successful correction ratio",
)


def update_rate_gauges() -> None:
    total_lookups = 0.0
    total_hits = 0.0
    for layer in ("exact", "semantic", "retrieval"):
        total_lookups += CACHE_LOOKUPS.labels(layer=layer)._value.get()
        total_hits += CACHE_HITS.labels(layer=layer)._value.get()

    CACHE_HIT_RATE.set((total_hits / total_lookups) if total_lookups else 0.0)

    total_verification = VERIFICATION_TOTAL._value.get()
    fail_verification = VERIFICATION_FAILURES._value.get()
    VERIFICATION_FAIL_RATE.set((fail_verification / total_verification) if total_verification else 0.0)

    total_correction = CORRECTION_TOTAL._value.get()
    success_correction = CORRECTION_SUCCESS._value.get()
    CORRECTION_RATE.set((success_correction / total_correction) if total_correction else 0.0)


def metrics_payload() -> tuple[bytes, str]:
    update_rate_gauges()
    return generate_latest(), CONTENT_TYPE_LATEST
