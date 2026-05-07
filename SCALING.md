# Scaling Strategy

This document outlines how the IT Support Copilot would evolve from its current
single-process prototype into a production deployment serving thousands of
concurrent users.

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Single Python Process (laptop / VM)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐    │
│  │  Streamlit  │     │  LangGraph  │     │     Chroma          │    │
│  │     UI      │────▶│   Runtime   │────▶│ (local persistent)  │    │
│  │ (port 8501) │     │ (in-process)│     │                     │    │
│  └─────────────┘     └─────────────┘     └─────────────────────┘    │
│        │                                        │                   │
│        │              ┌─────────────┐           │                   │
│        └─────────────▶│   OpenAI    │◀──────────┘                   │
│        │              │     API     │                               │
│        │              └─────────────┘                               │
│        │              ┌─────────────┐                               │
│        └─────────────▶│  Jira REST  │                               │
│                       │     API     │                               │
│                       └─────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Role | Current State |
|-----------|------|---------------|
| **Streamlit UI** | Ticket form + result + survey | Single process, in-memory session state |
| **LangGraph Runtime** | Agent orchestration | Compiled in-process, no checkpointing |
| **Chroma** | Vector store for runbook embeddings | Local sqlite + parquet, persistent on disk |
| **OpenAI API** | LLM + embeddings | External; rate-limited per project |
| **Jira REST API** | Ticket creation + transitions | External; per-instance throughput limit |

This is fine for a few concurrent users on a demo laptop. Production needs the
following evolutions.

---

## Containerization

Wrapping the app in Docker is the prerequisite for any horizontal scaling and
gives identical environments across dev/staging/prod.

### `Dockerfile`

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY knowledge_base/ ./knowledge_base/

# Build the vector index at image build time so the container is ready-to-run
RUN python scripts/ingest_kb.py

EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0"]
```

### `docker-compose.yml`

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JIRA_BASE_URL=${JIRA_BASE_URL}
      - JIRA_EMAIL=${JIRA_EMAIL}
      - JIRA_API_TOKEN=${JIRA_API_TOKEN}
      - JIRA_PROJECT_KEY=${JIRA_PROJECT_KEY}
    volumes:
      - chroma-data:/app/.chroma

volumes:
  chroma-data:
```

### Deploy

```bash
docker compose up -d
docker compose up --scale app=3 -d   # three replicas behind whatever LB sits in front
```

---

## Horizontal Scaling

### Application Layer

Streamlit's session state is per-connection in-memory, which means scaling out
to N replicas requires sticky sessions OR moving session state to a shared
store. Two clean paths:

#### Option A — Sticky sessions behind NGINX

```nginx
upstream copilot {
    ip_hash;             # Pin a client to a replica by IP
    server app1:8501;
    server app2:8501;
    server app3:8501;
}

server {
    listen 80;
    location / {
        proxy_pass http://copilot;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }
}
```

Trade-off: simple, but uneven traffic if many users come from one NAT.

#### Option B — Externalize session state to Redis

Move `st.session_state.history` and `st.session_state.user` into Redis keyed by
session ID. Any replica can serve any request. Requires a small Streamlit
helper or a switch to a stateless API + thin React/HTMX UI on top.

### Vector Store

Chroma local is fine for a few hundred chunks. As the runbook corpus grows or
multiple workspaces share an index, the recommended progression:

| Scale level | Vector backend | Why |
|-------------|----------------|-----|
| Demo (<10K chunks) | Chroma local (current) | Zero ops |
| Small (<100K chunks) | Chroma server in its own container | Multiple replicas can share one index |
| Medium (100K–1M) | Postgres + pgvector | Native auth, backups, replication |
| Large (1M+) | Pinecone / Weaviate / Qdrant Cloud | Sharding, rebalancing, sub-100ms p99 search |

The retriever in `src/rag/retriever.py` is wrapped behind a single `retrieve()`
function — swapping the backend means changing only `src/rag/ingest.py` and
`src/rag/retriever.py`, not agent code.

### Tool Layer

The MCP-shaped registry (`src/mcp/registry.py`) is already designed to be
swap-ready for real MCP servers. At scale, the local registry becomes the
client and tools live in dedicated processes:

```
┌──────────────┐     stdio/SSE     ┌──────────────────────┐
│  LangGraph   │ ◀───────────────▶ │  MCP Server: Jira    │
│  agents      │                   ├──────────────────────┤
│              │ ◀───────────────▶ │  MCP Server: Okta    │
│              │                   ├──────────────────────┤
│              │ ◀───────────────▶ │  MCP Server: Logs    │
└──────────────┘                   └──────────────────────┘
```

Each tool server can be scaled independently and deployed by whichever team
owns the underlying system (security team owns Okta tools, observability team
owns logs tools, etc.).

---

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: it-support-copilot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: it-support-copilot
  template:
    metadata:
      labels:
        app: it-support-copilot
    spec:
      containers:
      - name: app
        image: it-support-copilot:latest
        ports:
        - containerPort: 8501
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: copilot-secrets
              key: openai-api-key
        - name: JIRA_API_TOKEN
          valueFrom:
            secretKeyRef:
              name: copilot-secrets
              key: jira-api-token
        - name: JIRA_BASE_URL
          value: "https://yourorg.atlassian.net"
        resources:
          requests: { cpu: "500m", memory: "512Mi" }
          limits:   { cpu: "1500m", memory: "2Gi" }
        readinessProbe:
          httpGet: { path: /, port: 8501 }
          initialDelaySeconds: 10
        livenessProbe:
          httpGet: { path: /, port: 8501 }
          initialDelaySeconds: 30
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: it-support-copilot-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: it-support-copilot
  minReplicas: 2
  maxReplicas: 12
  metrics:
  - type: Resource
    resource:
      name: cpu
      target: { type: Utilization, averageUtilization: 70 }
---
apiVersion: v1
kind: Service
metadata:
  name: it-support-copilot
spec:
  selector: { app: it-support-copilot }
  ports:
  - port: 80
    targetPort: 8501
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: it-support-copilot
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  rules:
  - host: helpdesk.company.internal
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: it-support-copilot
            port: { number: 80 }
  tls:
  - hosts: [helpdesk.company.internal]
    secretName: copilot-tls
```

---

## Component-Specific Scaling

### LLM API (OpenAI)

OpenAI rate limits are per-key by tier. At scale, the bottlenecks are:

- **TPM (tokens per minute)** — gpt-4o-mini Tier 1 is 200K TPM. A typical
  Intake call uses ~600 tokens, Knowledge ~3000, Escalation ~2500. So a Tier-1
  key supports roughly 30–60 conversations/minute peak.
- **RPM (requests per minute)** — Tier 1 is 500 RPM. Typically not the
  bottleneck for our shape of traffic.

**Mitigations:**

```python
# Embed in src/llm.py with a tenacity-style retry-with-backoff
from openai import RateLimitError
from tenacity import retry, retry_if_exception_type, wait_exponential, stop_after_attempt

@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(min=1, max=30),
    stop=stop_after_attempt(5),
)
def safe_invoke(chain, payload):
    return chain.invoke(payload)
```

Cache hot Knowledge answers (the same "how do I reset my password?" gets asked
thousands of times):

```python
import hashlib, redis, json
cache = redis.Redis.from_url(os.environ["REDIS_URL"])

def cached_rag_answer(query: str, ttl_s: int = 3600) -> str | None:
    key = "rag:" + hashlib.sha256(query.lower().strip().encode()).hexdigest()
    hit = cache.get(key)
    return hit.decode() if hit else None

def store_rag_answer(query: str, answer: str, ttl_s: int = 3600) -> None:
    key = "rag:" + hashlib.sha256(query.lower().strip().encode()).hexdigest()
    cache.setex(key, ttl_s, answer)
```

Move classification to a smaller model (e.g., `gpt-4o-mini` is already minimal;
at higher scale, fine-tune a small open model for the Intake task and self-host
it on a single GPU).

### Jira API

Atlassian Cloud has per-tenant rate limits (~10 req/sec sustained,
~50 burst). At higher scale:

- **Batch ticket creation** — group adjacent escalations within a 5-second
  window into a single Jira call where possible.
- **Async ticket sync** — the agent returns the user's answer immediately and
  enqueues the Jira write to a worker queue (Celery / RQ / Kafka). Worker
  retries with backoff on rate-limit errors.
- **Escape-hatch** — switch the audit-ticket creation to "fire and forget" so
  Jira slowness doesn't block the user's response.

### Embeddings

Embedding requests are the cheapest and most parallelizable. Cache embeddings
of the user's query string as well as runbook chunks:

```python
def embed_with_cache(text: str) -> list[float]:
    key = "emb:" + hashlib.sha256(text.encode()).hexdigest()
    hit = cache.get(key)
    if hit:
        return json.loads(hit)
    vec = openai_client.embeddings.create(model=MODEL, input=text).data[0].embedding
    cache.setex(key, 86400, json.dumps(vec))
    return vec
```

---

## Caching Strategy

| Cache | Key | TTL | Hit-rate target |
|-------|-----|-----|-----------------|
| Final RAG answer | hash(normalized query) | 1 hour | 30–50% in steady state |
| Embedded query vector | hash(query) | 24 hours | 60–80% |
| Embedded runbook chunks | chunk_id | forever (until reingest) | 100% after first run |
| Intake classification | hash(message + user_dept) | 30 minutes | 20–30% |
| Jira transitions list | issue_type | 24 hours | ~99% (workflow rarely changes) |

Skip caching the **Escalation summary** — every escalation has unique context
and a stale summary is worse than a slightly slower fresh one.

---

## Session Management

For multi-replica deployments, move the Streamlit `session_state` (currently
the in-process `history` list and `user` context) to Redis:

```python
import streamlit as st
import redis, json, uuid

cache = redis.Redis.from_url(os.environ["REDIS_URL"])

def get_session_state(session_id: str) -> dict:
    raw = cache.get(f"session:{session_id}")
    return json.loads(raw) if raw else {"history": [], "user": None}

def save_session_state(session_id: str, state: dict) -> None:
    cache.setex(f"session:{session_id}", 1800, json.dumps(state))
```

Generate `session_id` per browser via a cookie or query param, persist on
every state change, expire after 30 minutes of inactivity.

---

## Monitoring & Observability

### Metrics to track

| Metric | Type | Alert threshold |
|--------|------|-----------------|
| Request latency p50 | Histogram | > 5s |
| Request latency p95 | Histogram | > 10s |
| Per-agent latency p95 | Histogram (one per agent) | Intake > 1.5s, Knowledge > 4s, Workflow > 5s, Escalation > 4s |
| Error rate | Counter / Gauge | > 1% |
| OpenAI 429 rate | Counter | > 0.5% |
| Jira 4xx/5xx rate | Counter | > 1% |
| Deflection rate (resolved without human) | Gauge | < 50% |
| Satisfaction (avg stars) | Gauge | < 4.0 |
| Active sessions | Gauge | > 80% capacity |
| Memory per pod | Gauge | > 85% |

### Stack

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    depends_on: [prometheus]

  loki:
    image: grafana/loki   # structured logs from each agent's TraceEvents

  alertmanager:
    image: prom/alertmanager
```

The `TraceEvent` model in `src/state.py` is already structured — pipe it into
Loki/CloudWatch as JSON so you can query "all conversations where Escalation
fired in the last hour" or "p95 Knowledge latency by office".

---

## Cost Optimization

### LLM Cost Reduction

1. **Smaller model for classification.** Intake is just structured output —
   could be served by a fine-tuned 1B-param open model on a single GPU.
   Frees 30% of OpenAI spend in steady state.
2. **Aggressive RAG caching.** A 40% cache hit on Knowledge answers is a 40%
   cost reduction on the most expensive call.
3. **Prompt compression.** Strip the natural-phrasing examples from the
   Intake prompt once a fine-tuned classifier exists.
4. **Batching embeddings.** OpenAI's embedding endpoint accepts arrays —
   re-ingest the entire knowledge base in a single API call.

### Infrastructure

1. **Auto-scale to zero overnight.** Most internal IT helpdesks see < 5%
   traffic between 8pm and 6am.
2. **Spot / preemptible nodes** for the Streamlit replicas. Sessions are
   externalized; pod restarts are a 2s blip.
3. **Reserved capacity** for the 2 replicas that always need to be up
   (`minReplicas: 2`); on-demand for the rest.

---

## Production Checklist

- [ ] Containerized with Dockerfile + docker-compose
- [ ] Sticky sessions or externalized session store (Redis)
- [ ] HorizontalPodAutoscaler configured (`min: 2, max: 12`)
- [ ] Vector store moved off local Chroma (Postgres+pgvector or managed)
- [ ] Tool layer migrated to real MCP servers (Jira/Okta/Logs as separate processes)
- [ ] Tenacity-style retry on OpenAI 429/5xx
- [ ] Async Jira sync via worker queue
- [ ] Redis-backed RAG-answer + embedding cache
- [ ] Prometheus + Grafana dashboards (latency p50/p95, deflection, satisfaction)
- [ ] Loki structured-log ingestion of TraceEvents
- [ ] Alertmanager rules (latency, error rate, deflection drop)
- [ ] Secrets in K8s `Secret` objects, not `.env` files
- [ ] TLS-terminating Ingress with cert-manager
- [ ] Backup strategy for the runbook corpus and any persistent state
- [ ] Disaster recovery runbook (what to do if OpenAI is down — fall back to escalation-only)
- [ ] Rate limiting on the public-facing Ingress (per-IP) to prevent abuse
