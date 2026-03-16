import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response.data,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }
  
  async sendQuery(query, grade, subject, studentId) {
    return this.client.post('/query', {
      query,
      grade,
      subject,
      student_id: studentId
    });
  }
  
  async optimizePrompt(prompt, model = 'gpt-3.5-turbo', tier = 'free') {
    return this.client.post('/optimize', {
      prompt,
      model,
      tier
    });
  }
  
  async getTextbook(subject, grade) {
    return this.client.get(`/textbook/${subject}/${grade}`);
  }
  
  async getMetrics() {
    return this.client.get('/metrics');
  }
  
  async healthCheck() {
    return this.client.get('/health');
  }
}

export const api = new ApiService();