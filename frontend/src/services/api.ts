import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status >= 500) {
      console.error('[API] Server error:', error.response.status, error.response.data);
    } else if (!error.response) {
      console.error('[API] Network error:', error.message);
    }
    return Promise.reject(error);
  },
);

export const challengeApi = {
  list: () => api.get('/challenges'),
  get: (id: string) => api.get(`/challenges/${id}`),
  getReference: (id: string) => api.get(`/challenges/${id}/reference-solution`),
};

export const submissionApi = {
  submit: (data: { challenge_id: string; code: string; mode: string }) =>
    api.post('/submissions', data),
  get: (id: number) => api.get(`/submissions/${id}`),
  submitSocraticAnswers: (submissionId: number, answers: string[]) =>
    api.post(`/submissions/${submissionId}/socratic-answers`, { answers }),
};

export const userApi = {
  getProfile: () => api.get('/user/profile'),
  getEloHistory: () => api.get('/user/elo-history'),
  getStats: () => api.get('/user/stats'),
  calibrate: (step: number) => api.post(`/user/calibrate?calibration_step=${step}`),
};

export default api;
