import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token wygasł lub nieprawidłowy - wyloguj
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// AUTH
// ============================================================================

export const login = async (email, password) => {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await api.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: JSON.stringify({
      username: email,
      password: password
    })
  });
  
  console.log('API RESPONSE:', response.data);
  return response.data;
};
export const logout = async () => {
  try {
    await api.post('/auth/logout');
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
};

// ============================================================================
// PATIENTS
// ============================================================================

export const createPatient = async (patientData) => {
  const response = await api.post('/patients/', patientData);
  return response.data;
};

export const getPatient = async (patientId) => {
  const response = await api.get(`/patients/${patientId}`);
  return response.data;
};

// ============================================================================
// TRIAGE
// ============================================================================

export const predictTriage = async (patientId) => {
  const response = await api.post('/triage/predict', { patient_id: patientId });
  return response.data;
};

export const getTriageStats = async () => {
  const response = await api.get('/triage/stats');
  return response.data;
};

// ============================================================================
// DEPARTMENTS
// ============================================================================

export const getDepartmentOccupancy = async () => {
  const response = await api.get('/departments/occupancy');
  return response.data;
};

// ============================================================================
// UTILS
// ============================================================================

export const setAuthToken = (token) => {
  localStorage.setItem('token', token);
};

export const getAuthToken = () => {
  return localStorage.getItem('token');
};

export default api;
