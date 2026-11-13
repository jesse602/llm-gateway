from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNT = Counter(
    "llm_gateway_requests_total",
    "Total requests handled by the gateway",
    ["route", "status"],
)

REQUEST_LATENCY = Histogram(
    "llm_gateway_request_duration_seconds",
    "End-to-end request latency including queue wait",
    ["route"],
)

QUEUE_DEPTH = Gauge(
    "llm_gateway_queue_depth",
    "Number of requests currently waiting for or holding a GPU slot",
)
