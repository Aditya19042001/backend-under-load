import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    memory_leak: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 20 },
        { duration: '5m', target: 20 },
      ],
    },
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:30000';

export default function () {
  const size = Math.floor(Math.random() * 20) + 10; // 10-30 MB
  const res = http.get(`${BASE_URL}/api/memory-leak?size_mb=${size}`);

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(2);
}