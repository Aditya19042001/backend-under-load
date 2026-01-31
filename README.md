# Backend Load Testing

A comprehensive FastAPI application for demonstrating backend system behavior under load, with intentional failure modes for learning and testing.

## 🏗️ Architecture

This project uses a **microservices architecture** with two separate repositories:

1. **[backend-load-testing](https://github.com/yourusername/backend-load-testing)** (this repo)
   - Main FastAPI application
   - Load testing scenarios
   - Kubernetes deployments
   - Monitoring and observability

2. **[downstream-slow-service](https://github.com/yourusername/downstream-slow-service)**
   - Mock external API service
   - Simulates slow downstream dependencies
   - Used for cascade failure testing

### Why Two Repositories?

✅ **Realistic microservices pattern** - Mimics production architecture  
✅ **Independent deployment** - Each service has its own lifecycle  
✅ **Version control** - Services can evolve independently  
✅ **Learning opportunity** - Practice inter-service communication  

## 🎯 Project Goals

- Understand how backend systems behave under different types of load
- Identify and demonstrate common bottlenecks (CPU, memory, I/O, database)
- Show how horizontal scaling changes failure modes
- Learn proper observability and monitoring techniques

## 📋 Prerequisites

- **Docker Desktop**
- **Minikube** (or other Kubernetes cluster)
- **kubectl**
- **k6** (load testing tool)
- **Python 3.11+**

### Quick Installation

```bash
# macOS
brew install minikube kubectl k6

# Ubuntu/Debian
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# 1. Clone this repository
git clone https://github.com/yourusername/backend-load-testing.git
cd backend-load-testing

# 2. Make scripts executable
chmod +x scripts/*.sh

# 3. Setup Minikube (downloads downstream repo automatically)
./scripts/setup-minikube.sh

# 4. Deploy everything
./scripts/deploy-all.sh

# 5. Run load tests
./scripts/load-test.sh
```

### Option 2: Manual Setup

```bash
# 1. Setup Minikube
./scripts/setup-minikube.sh

# 2. Deploy downstream service
./scripts/deploy-downstream.sh

# 3. Deploy main application
./scripts/deploy.sh

# 4. Verify deployment
kubectl get pods -n load-testing

# 5. Test connectivity
./scripts/test-downstream.sh
```

### Option 3: Local Development (Docker Compose)

```bash
# 1. Clone both repositories
git clone https://github.com/yourusername/backend-load-testing.git
git clone https://github.com/yourusername/downstream-slow-service.git

# 2. Create docker-compose.yml (see below)

# 3. Run all services
docker-compose up --build

# 4. Test
curl http://localhost:8000/health
curl http://localhost:8001/health
```

**docker-compose.yml** (for local development):
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: loadtest
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  downstream:
    build:
      context: ../downstream-slow-service
      dockerfile: docker/Dockerfile
    ports:
      - "8001:8001"
    environment:
      DEFAULT_DELAY: "3"

  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: "postgresql+asyncpg://postgres:postgres@postgres:5432/loadtest"
      REDIS_URL: "redis://redis:6379/0"
      DOWNSTREAM_SERVICE_URL: "http://downstream:8001"
    depends_on:
      - postgres
      - redis
      - downstream
```

## 📊 Available Endpoints

### Main Service (Port 8000)

#### Health & Metrics
- `GET /` - Service information
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

#### CPU-Bound Operations
- `GET /api/cpu-intensive?complexity=30` - Fibonacci calculation
- `GET /api/hash?iterations=10000` - CPU-intensive hashing
- `GET /api/json-processing?size=1000` - JSON serialization

#### I/O-Bound Operations
- `GET /api/slow?delay=5` - Simulated slow I/O
- `GET /api/random-delay` - Random delay
- `GET /api/blocking?duration=5` - Blocking operation
- `GET /api/parallel-io?count=5` - Parallel I/O

#### Downstream Dependencies
- `GET /api/call-downstream?timeout=5` - Call downstream service
- `GET /api/cascade-failure` - Multiple downstream calls
- `GET /api/no-timeout` - No timeout configured (dangerous)

#### Memory Operations
- `GET /api/memory-leak?size_mb=10` - Intentional memory leak
- `GET /api/memory-spike?size_mb=50` - Temporary spike
- `POST /api/clear-memory` - Clear memory leaks

#### Database Operations
- `POST /api/tasks` - Create task
- `GET /api/tasks?limit=10` - List tasks
- `GET /api/db-pool-exhaust?concurrent_queries=10` - Exhaust pool
- `GET /api/expensive-query?iterations=1000` - Expensive query

### Downstream Service (Port 8001 - Internal)
- `GET /slow?delay=5` - Configurable delay
- `GET /random` - Random delay
- `GET /sometimes-fail?failure_rate=0.3` - Random failures
- `GET /timeout-trap` - 60 second response

## 🧪 Load Testing Scenarios

### 1. Baseline Performance
```bash
k6 run load-tests/k6/baseline.js
```
**Purpose**: Establish baseline metrics  
**Metrics**: RPS, latency (p50, p95, p99), error rate

### 2. CPU Stress
```bash
k6 run load-tests/k6/cpu-stress.js
```
**Purpose**: Demonstrate CPU throttling  
**Observation**: Response degradation, CPU limits

### 3. Memory Stress
```bash
k6 run load-tests/k6/memory-stress.js
```
**Purpose**: Demonstrate OOM kills  
**Observation**: Pod restarts, memory limits

### 4. I/O Stress
```bash
k6 run load-tests/k6/io-stress.js
```
**Purpose**: Worker pool exhaustion  
**Observation**: Request queuing, timeouts

### 5. Database Pool Exhaustion
```bash
k6 run load-tests/k6/db-pool-exhaust.js
```
**Purpose**: Connection pool limits  
**Observation**: Connection wait times, timeouts

### 6. Cascade Failure
```bash
k6 run load-tests/k6/cascade-failure.js
```
**Purpose**: Downstream failure propagation  
**Observation**: How failures cascade upstream

## 📈 Monitoring

### View Metrics
```bash
# Prometheus metrics
curl http://$(minikube ip):30000/metrics

# Pod resource usage
kubectl top pods -n load-testing

# Watch HPA scaling
kubectl get hpa -n load-testing --watch
```

### View Logs
```bash
# Main application
kubectl logs -f deployment/backend-app -n load-testing

# Downstream service
kubectl logs -f deployment/downstream-service -n load-testing

# All services
stern -n load-testing .
```

### Real-time Monitoring
```bash
./scripts/monitor.sh --watch
```

## 🎓 Learning Scenarios

### Scenario 1: CPU Throttling
```bash
# Limit CPU to 100m
kubectl set resources deployment backend-app -n load-testing --limits=cpu=100m

# Run CPU stress test
k6 run load-tests/k6/cpu-stress.js

# Observe: Response times increase, CPU at 100%, throttling
```

### Scenario 2: OOMKilled
```bash
# Run memory leak test
for i in {1..20}; do
  curl "http://$(minikube ip):30000/api/memory-leak?size_mb=50"
  sleep 2
done

# Observe: kubectl get pods --watch shows OOMKilled
```

### Scenario 3: Downstream Service Failure
```bash
# Stop downstream service
kubectl scale deployment downstream-service -n load-testing --replicas=0

# Try cascade endpoint
curl "http://$(minikube ip):30000/api/cascade-failure"

# Observe: All requests fail, timeouts, error propagation
```

### Scenario 4: Horizontal Scaling
```bash
# Enable HPA
kubectl apply -f k8s/hpa.yaml

# Generate load
k6 run --vus 100 --duration 10m load-tests/k6/baseline.js

# Watch scaling
kubectl get hpa -n load-testing --watch
# Observe: Replicas increase 1 → 10, latency improves
```

## 🔧 Common Commands

```bash
# Get service URL
minikube service backend-service -n load-testing --url

# Port forward for debugging
kubectl port-forward svc/backend-service 8000:8000 -n load-testing

# Restart deployment
kubectl rollout restart deployment/backend-app -n load-testing

# Scale manually
kubectl scale deployment backend-app -n load-testing --replicas=5

# View events
kubectl get events -n load-testing --sort-by='.lastTimestamp'

# Describe pod issues
kubectl describe pod <pod-name> -n load-testing

# Exec into pod
kubectl exec -it <pod-name> -n load-testing -- /bin/bash
```

## 📊 Key Metrics to Track

| Metric | Description | Target |
|--------|-------------|--------|
| **Request Rate** | Requests/second | > 100 RPS |
| **Latency p95** | 95th percentile | < 500ms |
| **Latency p99** | 99th percentile | < 1000ms |
| **Error Rate** | Failed requests % | < 0.1% |
| **CPU Usage** | % of limit | < 80% |
| **Memory Usage** | % of limit | < 80% |

## 🐛 Troubleshooting

### Pods Not Starting
```bash
kubectl describe pod <pod-name> -n load-testing
kubectl logs <pod-name> -n load-testing
```

**Common issues:**
- Image not found: Run `./scripts/setup-minikube.sh` again
- Database not ready: Wait longer or check postgres pod
- Downstream service missing: Run `./scripts/deploy-downstream.sh`

### Downstream Service Connection Failed
```bash
# Test connectivity
./scripts/test-downstream.sh

# Check service
kubectl get svc downstream-service -n load-testing

# Check endpoints
kubectl get endpoints downstream-service -n load-testing
```

### Load Tests Failing
```bash
# Verify service accessible
curl http://$(minikube ip):30000/health

# Check NodePort
kubectl get svc backend-service -n load-testing
```

## 🧹 Cleanup

```bash
# Delete all resources
./scripts/cleanup.sh

# Or manually
kubectl delete namespace load-testing

# Stop Minikube
minikube stop

# Delete cluster
minikube delete
```

## 📝 Project Structure

```
backend-load-testing/
├── app/                    # Main FastAPI application
├── k8s/                    # Kubernetes manifests
├── docker/                 # Dockerfile
├── load-tests/            # K6 test scripts
├── scripts/               # Automation scripts
└── README.md
```

**Related Repository**: [downstream-slow-service](https://github.com/yourusername/downstream-slow-service)

## 🎯 LinkedIn Content Plan

This project demonstrates 6 key concepts for LinkedIn posts:

1. **Architecture & Setup** - Two-repo microservices structure
2. **CPU & Memory Limits** - Resource exhaustion scenarios
3. **Concurrency Issues** - Connection pools, worker limits
4. **Distributed Failures** - Cascade failures, timeouts
5. **Scaling Strategies** - HPA in action, when scaling helps
6. **Lessons Learned** - Production-ready best practices

## 🤝 Contributing

This is a learning project. Feel free to:
- Fork and experiment
- Add new failure scenarios
- Improve documentation
- Share your findings

## 📄 License

MIT License

## 🔗 Links

- **Downstream Service**: [downstream-slow-service](https://github.com/yourusername/downstream-slow-service)
- **Author**: Your Name
- **LinkedIn**: [Your Profile](#)
- **Blog Posts**: Coming soon!

---

**Happy Load Testing! 🚀**

Remember: The goal is to learn how systems fail so you can build better, more resilient production systems.