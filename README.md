# llm-gateway

A self-hosted, OpenAI-API-compatible gateway in front of local LLMs running on
[Ollama](https://ollama.com). It adds the things a raw Ollama instance doesn't
have: API-key auth, per-key rate limiting, a bounded request queue so a single
GPU doesn't fall over under concurrent load, and Prometheus metrics.

Status: 🚧 in progress — see commit history for build-in-public steps.

## Why

Ollama alone is a great inference server but has no auth, no rate limiting,
and no backpressure — concurrent requests just pile onto the GPU. This wraps
it with the production concerns you'd actually need to expose it as a service.

## Architecture

```
Client ──HTTPS──> [Gateway: FastAPI, k3s] ──LAN──> [Ollama: bare-metal macOS]
                        │
                        ├─ API key auth
                        ├─ rate limiter (per key)
                        ├─ bounded concurrency queue
                        └─ /metrics ──> Prometheus ──> Grafana
```

Ollama runs **bare-metal** on the host (Apple Silicon GPU access doesn't
pass through into a Linux VM/container), while the gateway and observability
stack run in **real Kubernetes** (k3s via colima) and reach Ollama over the
LAN. This mirrors how GPU inference infra is actually split in practice:
stateless control-plane services in orchestration, GPU workloads pinned to
bare metal.

## Stack

- **FastAPI** — gateway service
- **Ollama** — local model inference
- **Prometheus + Grafana** — metrics and dashboards
- **Docker** — containerized gateway image
- **k3s (via colima)** — deployment target
- **GitHub Actions** — CI (lint, test, build/push image)

## Local dev

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

OpenAI-compatible chat endpoint:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $LLM_GATEWAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.1:8b", "messages": [{"role": "user", "content": "hi"}]}'
```

## Deployment

See [`k8s/`](k8s/) for manifests and [`docs/deploy.md`](docs/deploy.md) for
the deployment runbook.

## License

MIT
