import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  scenarios: {
    cpu_stress: {
      executor: 'constant-arrival-rate',
      rate: 50,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 50,
      maxVUs: 100,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<5000'],
    errors: ['rate<0.2'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:30000';

export default function () {
  const complexity = Math.floor(Math.random() * 10) + 25; // Random 25-35
  const res = http.get(`${BASE_URL}/api/cpu-intensive?complexity=${complexity}`);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 5000ms': (r) => r.timings.duration < 5000,
  });

  errorRate.add(res.status !== 200);
  sleep(0.5);
}