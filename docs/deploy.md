# Deployment runbook

## Environment

- **Ollama** runs bare-metal on macOS (`brew services start ollama`), since
  Apple Silicon GPU access doesn't pass through into a Linux VM or container.
- **k3s** runs via [colima](https://github.com/abiosoft/colima)
  (`colima start --kubernetes`), which gives a real single-node Kubernetes
  cluster in a lightweight Lima VM on the same machine.
- The two talk over `host.lima.internal`, which colima's VM resolves to the
  macOS host.

## One-time cluster setup

```bash
brew install ollama colima kubectl docker
brew services start ollama
ollama pull llama3.1:8b
colima start -f --cpu 4 --memory 8 --kubernetes
```

## Building and shipping the image

CI (`.github/workflows/ci.yml`) lints, tests, and pushes
`ghcr.io/jesse602/llm-gateway:latest` on every push to `main` — that's the
real path for a production deploy with a registry pull secret.

For this homelab cluster, GHCR auth isn't wired into the single-node k3s, so
the image is built and imported directly into containerd instead (no
registry round-trip needed for a local demo):

```bash
docker build -t ghcr.io/jesse602/llm-gateway:latest .
docker save ghcr.io/jesse602/llm-gateway:latest -o /tmp/llmgw.tar
mv /tmp/llmgw.tar ~/llmgw.tar   # into colima's mounted home dir
colima ssh -- sudo ctr -n k8s.io images import /Users/<you>/llmgw.tar
```

`k8s/deployment.yaml` uses `imagePullPolicy: IfNotPresent` so the kubelet
uses the image already sitting in containerd instead of trying to pull it.

## Deploying

```bash
kubectl apply -f k8s/namespace.yaml
kubectl create secret generic llm-gateway-secrets -n llm-gateway \
  --from-literal=LLM_GATEWAY_API_KEYS=<your-key>
kubectl apply -f k8s/configmap.yaml -f k8s/deployment.yaml -f k8s/service.yaml
```

## Verifying

```bash
kubectl get pods -n llm-gateway
kubectl port-forward -n llm-gateway svc/llm-gateway 8080:80
curl http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer <your-key>" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.1:8b", "messages": [{"role": "user", "content": "hi"}]}'
```

## Observability (local, via docker-compose)

```bash
docker compose up prometheus grafana
```

Grafana: http://localhost:3000 (admin/admin), Prometheus datasource is
pre-provisioned. Gateway exposes `/metrics` for scraping.
