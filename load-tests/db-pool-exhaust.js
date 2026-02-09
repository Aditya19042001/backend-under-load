import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    db_pool: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { target: 50, duration: '1m' },  // Ramp to 50 VUs
        { target: 100, duration: '2m' }, // Spike to 100 VUs
        { target: 50, duration: '1m' },  // Back down
      ],
    },
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:30000';

export default function () {
  const res = http.get(`${BASE_URL}/api/db-pool-exhaust?concurrent_queries=30`, {
    timeout: '30s',
  });

  check(res, {
    'status is not 500': (r) => r.status !== 500,
  });

  sleep(0.1); // Minimal sleep to maximize concurrent load
}