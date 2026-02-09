# Backend Under Load: Watching Systems Fail (So You Learn)

Most of us know backend systems fail under load. Fewer of us have actually watched them fail.

So I decided to build a small, controlled setup to observe how backend systems behave when pushed in different ways: CPU pressure, memory pressure, slow downstreams, and database bottlenecks.

This post explains what I built, what I tested, what I observed, and the core lessons.

## My Setup (Simple but Intentional)

I kept everything small and constrained so failures would appear quickly and clearly.

### Infrastructure

- **Minikube** – local Kubernetes cluster for realistic distributed setup
- **FastAPI Backend Service** – Python application with multiple stress test endpoints
- **PostgreSQL** – with a limited connection pool
- **k6** – for load testing
- **Prometheus + Grafana** – for monitoring

### Resource Limits

Each service was deliberately throttled:

```yaml
requests:
  cpu: "250m"
  memory: "256Mi"
limits:
  cpu: "500m"
  memory: "512Mi"
```

This makes failures visible faster, which is perfect for learning.

### 📊 Monitoring & Observability Setup

#### Prometheus & Grafana Deployment

To understand how the system behaves under load, I deployed Prometheus and Grafana in their own namespace alongside the application:

```bash
# Create separate namespace for monitoring
kubectl create namespace monitoring
```

**Prometheus** was configured to:
- Scrape metrics from the FastAPI backend application's `/metrics` endpoint every 15 seconds
- Collect the following key metrics:
  - HTTP request duration and response times
  - Error rates and failed requests
  - Active database connections
  - Memory and CPU usage
  - Custom application metrics (complexity scores, memory allocations, etc.)

The backend deployment includes Prometheus annotations for auto-discovery:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

A `ServiceMonitor` resource tells Prometheus what to scrape:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-app-monitor
  namespace: load-testing
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: http
    interval: 15s
    path: /metrics
```

#### Accessing Grafana Dashboard

Once Grafana and Prometheus were deployed in the monitoring namespace, I used port-forwarding to access the dashboard locally:

```bash
# Port-forward Grafana to localhost
kubectl port-forward -n monitoring svc/grafana 3000:80

# Now open http://localhost:3000 in your browser
# (Default credentials: admin/admin)
```

This allowed me to view real-time dashboards showing:
- CPU and memory usage trends
- Request latency percentiles (p50, p95, p99)
- Error rate spikes during load tests
- Pod restart events (OOM kills, CPU throttling)
- Database connection pool utilization

The beauty of this setup was **the instant visibility into system behavior**. When CPU spiked or memory was exhausted, it was immediately obvious in the graphs. This visual feedback was essential for understanding the root cause of each failure mode.

---

## 🧪 Load Tests I Ran

I created different k6 scripts, each designed to stress the system in a specific way. Each test provides distinct insights into how the system degrades.

### 1️⃣ Baseline Test (`baseline.js`)

**What it does:**
- Simulates realistic traffic with 50-100 concurrent users over 16 minutes
- Makes batch requests to fast endpoints (`/api/fast`, `/api/ping`, `/health`)
- Gradually ramps up and down to observe smooth performance degradation

**Load pattern:**
- 2 min ramp-up to 50 users
- 5 min steady at 50 users
- 2 min ramp-up to 100 users
- 5 min steady at 100 users
- 2 min ramp-down

**What this teaches:**
- Establishes the system's normal operating parameters
- Provides a baseline to compare against stress tests
- Shows how long the system takes to recover

---

### 2️⃣ CPU-Intensive Load (`cpu-stress.js`)

**What it does:**
- Sends 50 requests per second for 5 minutes
- Each request triggers heavy computation (fibonacci calculations or similar) with random complexity (25-35 iterations)
- Maintains 50-100 pre-allocated virtual users

**Load pattern:**
- Constant arrival rate of 50 req/s
- Max 100 concurrent virtual users
- 5 minute test duration

**What I observed:**
- CPU usage spiked rapidly to 100%
- Response times increased from <100ms to several seconds
- Error rates began climbing after ~2 minutes
- Requests eventually timed out as CPU throttling became severe
- Pod remained "running" but was functionally unusable

**What this teaches:**
- CPU saturation increases latency before causing complete failure
- Even if the pod is "up," it may already be unusable to clients
- CPU pressure degrades gracefully at first, then fails hard
- Monitoring latency trends reveals CPU pressure before errors spike

---

### 3️⃣ Memory-Intensive Load (`memory-stress.js`)

**What it does:**
- Ramps up to 20 concurrent users over 2 minutes
- Each request allocates 10-30 MB of memory
- Stays at 20 users for 5 minutes, continuously allocating memory

**Load pattern:**
- Ramping-VUs scenario: gradually increase to 20 concurrent users
- Each user allocates significant memory per request
- Minimal sleep between requests

**What I observed:**
- Memory usage climbed steadily and predictably
- After ~3 minutes, memory reached the 512Mi limit
- Kubernetes killed the pod with OOM (Out Of Memory) error
- Requests started failing abruptly (connection resets)
- Pod restarted automatically after ~30 seconds
- Subsequent requests failed again as memory pressure returned

**What this teaches:**
- Memory pressure causes hard, unrecoverable failures (unlike CPU)
- Memory exhaustion doesn't degrade gracefully—it crashes instantly
- OOM kills are visible in Kubernetes events but often missed in logs
- Tight memory limits expose wasteful allocation patterns quickly
- Memory pressure is harder to recover from than CPU pressure

---

### 4️⃣ Cascading Failure Test (`cascade-failure.js`)

**What it does:**
- The load test service calls the `/api/cascade-failure` endpoint
- This endpoint makes downstream HTTP calls to a slow external service
- Simulates the cascading effect of one slow dependency bringing down the entire system
- Ramps from 50 to 100 req/s over 7 minutes with timeouts at 30 seconds

**Load pattern:**
- Ramping arrival rate from 10 req/s to 100 req/s
- Simulates slow downstream service responses
- 30-second timeouts to prevent indefinite hangs

**What I observed:**
- Initial requests completed normally (~500-1000ms)
- As load increased, downstream latency worsened
- Thread pools in the main service started filling up with waiting requests
- Latency for **unrelated request streams** started increasing
- Throughput dropped sharply as more threads blocked waiting for downstream responses
- Eventually, all requests started failing or timing out
- The healthy service became unusable due to a single slow dependency

**What this teaches:**
- One slow dependency can bring down a healthy service
- Cascading failures happen silently until throughput collapses—there's no early warning
- Thread pools are easily exhausted by slow external calls
- Connection pool exhaustion in dependent services multiplies the impact
- **Timeouts and circuit breakers are not optional**—they're critical defenses

---

### 5️⃣ Database Connection Pool Exhaustion (`db-pool-exhaust.js`)

**What it does:**
- Ramps from 50 to 100 virtual users over 4 minutes
- Each request makes 30 concurrent database queries
- Designed to exhaust the limited PostgreSQL connection pool
- Minimal sleep (100ms) between requests to maximize concurrent load

**Load pattern:**
- Ramping virtual users: 50 → 100 → 50 over 4 minutes
- 30 concurrent DB queries per request
- High concurrency to stress database connections

**What I observed:**
- Initial requests succeeded (database has 20-30 connection pool)
- After ~1-2 minutes, new requests started queuing
- Requests began timing out waiting for available connections
- Adding more replicas made things **worse**, not better:
  - Each pod got its own connection pool
  - 3 pods × 5 connections = 15 total connections to shared PostgreSQL
  - More pods = more processes competing for the same small pool
- Error rates increased exponentially as more pods were added

**What this teaches:**
- Databases are often the real bottleneck in system performance
- Scaling stateless services can make things worse if the database isn't scaled too
- Connection pool exhaustion is a hard limit that scaling doesn't solve
- **More pods = more DB connections = faster exhaustion**
- Horizontal scaling requires proportional database scaling
- Connection pool limits are a critical resource constraint

---

### 6️⃣ I/O-Intensive Load (`io-stress.js`)

**What it does:**
- Maintains 30 concurrent virtual users
- Each request calls a `/api/slow` endpoint with a 3-8 second delay (simulating external I/O like API calls, file operations, or network requests)
- 5-minute test duration with 1-second sleep between requests

**Load pattern:**
- Constant 30 VUs (constant-vus scenario)
- Variable response delay to simulate realistic I/O variability
- 5-minute test duration

**What I observed:**
- Response times were consistently 3-8+ seconds (dominated by I/O delay)
- Low error rates but high latency
- Memory usage remained stable
- CPU usage was moderate
- The bottleneck was network I/O, not compute resources
- Requests queued naturally but didn't fail

**What this teaches:**
- I/O delays dominate response times and are harder to optimize through scaling
- I/O-bound systems need connection pooling and async handling, not more CPU
- Unlike CPU or memory pressure, I/O delays don't cause crashes—they cause slowness
- Users experience degraded performance long before errors appear
- I/O-bound systems need different scaling strategies (connection pooling, async patterns)

---

## 📊 Monitoring Results

Throughout these tests, **Prometheus + Grafana provided critical visibility:**

**Metrics that mattered:**
- **Latency trends**: Early indicator of system stress
- **Error rates**: Hard indicator of failure
- **Resource utilization**: CPU (%) and Memory (Mi)
- **Pod restart events**: Visible as gaps in metric graphs
- **Active connections**: Showed connection pool saturation

**Key observation:** When I could see the system struggling in the graphs (CPU spikes, memory climbing, latency increasing), it was obvious *why* failures occurred. Without this visibility, I'd just see "request timeout" and have no idea why.

---

## 🔍 Big Lessons

### ✅ Systems fail in different ways

- **CPU pressure** → Slow responses, eventually timeouts
- **Memory pressure** → Guaranteed crashes (OOM kills)
- **Slow dependencies** → Cascading failures, resource exhaustion
- **DB bottlenecks** → Scaling backfires, silent failures

### ✅ Scaling is not a magic solution

- **Scaling helps** when the bottleneck is CPU (distribute compute load)
- **Scaling hurts** when the bottleneck is stateful resources:
  - Database connection pools get exhausted faster
  - More pods = more state to manage
  - Coordination overhead increases
- **Scaling multiplies both capacity AND mistakes**
- Need to measure: "What resource are we actually limited by?"

### ✅ Resource limits are your best teacher

- Tight limits expose problems early
- They force you to understand your resource consumption
- They reveal inefficient patterns quickly (memory waste, connection leaks)
- They're the difference between learning in development and failing in production

### ✅ Observability changes how you think

- Numbers explain behavior better than logs
- Latency is often the first warning sign (before errors appear)
- Visual graphs (Prometheus/Grafana) make patterns obvious
- Metrics from Kubernetes (restarts, evictions) provide crucial context

### ✅ Different failure modes need different solutions

| Failure Mode | Root Cause | Solution |
|---|---|---|
| High latency (CPU bound) | CPU exhaustion | Optimize code, cache, or scale horizontally |
| Crashes (OOM) | Memory waste | Reduce allocations, stream data, use pagination |
| Cascading failures | Slow dependencies | Timeouts, circuit breakers, bulkheads |
| Connection timeouts | DB pool exhaustion | Increase pool size, connection pooling, scale DB |

---

## 🚀 Why This Exercise Matters

This small setup helped me understand:

1. **Why "it works on my machine" means nothing under load**
   - Local machines have different resource profiles
   - Load exposes race conditions and resource limits invisible in dev

2. **Why production issues are rarely caused by a single bug**
   - Failures are usually about resource exhaustion or cascading effects
   - Multiple small inefficiencies compound under load

3. **Why backend engineering is about behavior, not just code**
   - Understanding *how* your system fails matters more than knowing the code
   - Observability is as important as functionality
   - Design decisions have load-test consequences

4. **How to think about scaling decisions**
   - Scaling isn't always the answer
   - You need to understand your bottleneck first
   - Resource limits force clarity

---

## 📚 Key Takeaways for Backend Engineers

If you're a backend developer and haven't intentionally broken your own system, I highly recommend doing it.

**You'll learn more in one weekend than in months of theory.**

The steps:
1. Build a small, resource-constrained system
2. Deploy it somewhere observable (Minikube + Prometheus/Grafana)
3. Run targeted stress tests (load, memory, chaos)
4. Watch it fail
5. **Understand why it failed**

The insights you gain will fundamentally change how you design, deploy, and operate backends. You'll understand why certain architectural patterns exist, why resource limits matter, and why observability is non-negotiable.

Most importantly, you'll stopped being afraid of failure and start expecting it—designing for it proactively instead of reacting to it in production.

---

## 📖 References

- **k6 Documentation**: https://k6.io/docs/
- **Prometheus Monitoring**: https://prometheus.io/docs/
- **Grafana Dashboards**: https://grafana.com/docs/
- **Kubernetes Resource Management**: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- **Site Reliability Engineering (SRE) Book**: https://sre.google/sre-book/

