import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    db_pool: {
      executor: 'constant-vus',
      vus: 20, // More than DB pool size (5)
      duration: '3m',
    },
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:30000';

export default function () {
  const res = http.get(`${BASE_URL}/api/db-pool-exhaust?concurrent_queries=15`);

  check(res, {
    'status is not 500': (r) => r.status !== 500,
  });

  sleep(2);
}