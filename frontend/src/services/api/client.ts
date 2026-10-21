import axios from "axios";

const baseURL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api/v1";

export const apiClient = axios.create({
  baseURL,
  timeout: 60000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Unexpected API error";

    console.error("API ERROR:", error);

    return Promise.reject(new Error(message));
  }
);