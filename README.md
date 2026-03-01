# Math Tutor Hybrid Workflow Orchestrator

Production-grade FastAPI microservice cho Hybrid Math Engine:

- Retrieval: ChromaDB
- Reasoning: Qwen2.5-Coder-7B (Ollama GPU)
- Deterministic verification: SymPy sandbox
- Vietnamese formatting: Sailor2-1B (Ollama CPU)
- Multi-layer cache: Redis exact + semantic + retrieval cache

## Project structure

```text
workflow-api/
├── app/
│   ├── clients/
│   ├── config/
│   ├── middleware/
│   ├── models/
│   ├── routers/
│   ├── services/
│   └── main.py
├── deploy/nginx.conf
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── main.py
```

## Run local

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

## Core pipeline (`POST /api/v1/workflow/chat`)

1. Input validation + prompt injection guard
2. Cache lookup: exact -> semantic -> retrieval
3. Chroma retrieval
4. Qwen reasoning JSON (`reasoning_steps`, `final_answer`, `python_code`, `confidence_score`)
5. SymPy sandbox execution + deterministic verification
6. Optional self-correction loop (1 retry)
7. Sailor2 formatting + LaTeX sanitize
8. Cache write-back

## API test cURL

### 1) Workflow full pipeline

```bash
curl -X POST http://localhost/api/v1/workflow/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Giải phương trình bậc hai x^2 - 5x + 6 = 0","level":"THPT","stream":false}'
```

### 2) Workflow streaming

```bash
curl -N -X POST http://localhost/api/v1/workflow/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Tính đạo hàm của f(x)=x^3+2x","level":"THPT","stream":true}'
```

### 3) Retrieval only

```bash
curl -X POST http://localhost/api/v1/rag-only \
  -H "Content-Type: application/json" \
  -d '{"question":"Định lý Viète","level":"THPT"}'
```

### 4) Math only

```bash
curl -X POST http://localhost/api/v1/math-only \
  -H "Content-Type: application/json" \
  -d '{"question":"Giải hệ phương trình tuyến tính 2 ẩn","level":"THPT"}'
```

### 5) Format only

```bash
curl -X POST http://localhost/api/v1/format-only \
  -H "Content-Type: application/json" \
  -d '{"question":"Giải bất phương trình bậc nhất","level":"THCS"}'
```

### 6) Health + Metrics

```bash
curl http://localhost/api/v1/health/live
curl http://localhost/api/v1/health/ready
curl http://localhost/metrics
```

### 7) Verify only

```bash
curl -X POST http://localhost/api/v1/verify-only \
  -H "Content-Type: application/json" \
  -d '{"question":"Giải phương trình x^2-5x+6=0","level":"THPT","stream":false}'
```

### 8) Cache stats

```bash
curl http://localhost/api/v1/cache/stats
```

### 9) Cache clear

```bash
curl -X POST http://localhost/api/v1/cache/clear
```

## Docker Compose

```bash
docker compose up -d --build
```

Services gồm: `workflow-api`, `chromadb`, `ollama-gpu`, `ollama-viet`, `redis`, `nginx`.

## Example metrics output (rút gọn)

```text
workflow_api_cache_hit_rate 0.73
workflow_api_verification_fail_rate 0.11
workflow_api_correction_rate 0.67
workflow_api_avg_reasoning_time_seconds_bucket{le="2.0"} 54
workflow_api_avg_verification_time_seconds_bucket{le="0.5"} 71
workflow_api_stage_latency_seconds_bucket{stage="verification",le="0.5"} 69
```
