import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    io_stress: {
      executor: 'constant-vus',
      vus: 30,
      duration: '5m',
    },
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:30000';

export default function () {
  const delay = Math.floor(Math.random() * 5) + 3; // 3-8 seconds
  const res = http.get(`${BASE_URL}/api/slow?delay=${delay}`);

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(1);
}