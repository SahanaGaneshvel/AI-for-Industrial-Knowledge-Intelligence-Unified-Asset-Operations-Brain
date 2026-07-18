import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const copilotApi = {
  query: async (query, top_k = 8) => {
    const response = await api.post('/query', { query, top_k });
    return response.data;
  },
};

export const complianceApi = {
  runScan: async () => {
    const response = await api.get('/compliance/scan');
    return response.data;
  },
  getReport: async () => {
    const response = await api.get('/compliance/report');
    return response.data;
  },
};

export const graphApi = {
  getGraph: async () => {
    const response = await api.get('/graph');
    return response.data;
  },
  getNode: async (nodeId, hops = 1) => {
    const response = await api.get(`/graph/node/${encodeURIComponent(nodeId)}?hops=${hops}`);
    return response.data;
  },
  getStats: async () => {
    const response = await api.get('/graph/stats');
    return response.data;
  },
};

export const ingestApi = {
  runFullIngestion: async (force = false) => {
    const response = await api.post(`/ingest?force=${force}`);
    return response.data;
  },
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/ingest/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export const healthApi = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
