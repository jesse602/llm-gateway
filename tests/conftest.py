import os

os.environ["LLM_GATEWAY_API_KEYS"] = "test-key"
os.environ["RATE_LIMIT_REQUESTS"] = "3"
os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "60"
os.environ["MAX_CONCURRENCY"] = "2"
