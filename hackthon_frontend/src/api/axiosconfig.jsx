import axios from "axios";
import store from '../store/store'

import {
  destroyDetails,
  setUserDetails,
  updateAccessToken,
} from "../store/UserDetailsSlice";
import history from "../History";
import { toast } from "react-toastify";

const baseurl = import.meta.env.VITE_BASE_URL;

const axiosInstance = axios.create({
  baseURL: `${baseurl}`,
});

// Request interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    const state = store.getState();
    const accessToken = state.userDetails.access_token;

    if (accessToken) {
      config.headers["Authorization"] = `Bearer ${accessToken}`;
    }
    return config;
  },

  (error) => {
    Promise.reject(error);
  }
);

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Skip processing for auth-related endpoints
    if (
      originalRequest.url?.includes("/refresh_token") ||
      originalRequest.url?.includes("/login")
    ) {
      return Promise.reject(error);
    }

    // Handle 401 errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Refresh token request
        const refreshResponse = await axios.post(
          `${baseurl}/users/refresh_token`,
          {},
          { withCredentials: true }
        );

        // Extract new access token
        const newAccessToken = refreshResponse.data?.access_token;

        if (!newAccessToken) {
          throw new Error("Missing access token in refresh response");
        }

        // Update ONLY the access token in Redux
        store.dispatch(updateAccessToken(newAccessToken));

        // Update request header and retry
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        console.error("Token refresh failed:", refreshError);

        // Full logout process
        store.dispatch(destroyDetails());
        try {
          await axios.post(
            `${baseurl}/users/logout`,
            {},
            { withCredentials: true }
          );
        } catch (e) {
          console.error("Logout failed:", e);
        }

        // Notify user
        toast.error("Your session has expired. Please log in again.", {
          position: "bottom-center",
          autoClose: 5000,
        });

        // Redirect to login
        history.push("/login");
        return Promise.reject(refreshError);
      }
    }

    // Handle other errors
    if (error.response?.status === 403) {
      toast.error("You don't have permission for this action", {
        position: "bottom-center",
      });
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
