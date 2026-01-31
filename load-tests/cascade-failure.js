import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    cascade: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 200,
      stages: [
        { target: 50, duration: '2m' },
        { target: 100, duration: '3m' },
        { target: 50, duration: '2m' },
      ],
    },
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:30000';

export default function () {
  const res = http.get(`${BASE_URL}/api/cascade-failure`, {
    timeout: '30s',
  });

  check(res, {
    'status is 200 or 504': (r) => r.status === 200 || r.status === 504,
  });

  sleep(1);
}
