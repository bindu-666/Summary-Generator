const API_BASE_URL = 'http://localhost:5000';

export const API_ENDPOINTS = {
    AUTH: {
        LOGIN: `${API_BASE_URL}/api/auth/login`,
        SIGNUP: `${API_BASE_URL}/api/auth/signup`,
    },
    UPLOAD: `${API_BASE_URL}/upload`,
    GENERATE: `${API_BASE_URL}/generate`,
};

export default API_BASE_URL; 