import axios from "axios";
import store from '../store/store'
import publicAxiosInstance from './publicAxiosconfig';

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
  withCredentials: true,
});

// Request interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    const state = store.getState();
    const accessToken = state.userDetails.access_token;

    if (accessToken) {
      config.headers["Authorization"] = `Bearer ${accessToken}`;
      console.log("Request interceptor - Token being sent:", accessToken.substring(0, 20) + "...");
    } else {
      console.log("Request interceptor - No access token found in state");
      console.log("Current state:", state.userDetails);
    }
    return config;
  },

  (error) => {
    return Promise.reject(error);
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

    // Handle 401 errors (including JWT token validation errors)
    if (error.response?.status === 401 && !originalRequest._retry) {
      console.log("401 error received, attempting token refresh:", error.response.data);
      originalRequest._retry = true;

      try {
        // Refresh token request
        console.log("Attempting to refresh token...");
        const refreshResponse = await publicAxiosInstance.post(
          '/api/auth/refresh_token',
          {}
        );

        // Extract new access token
        console.log("Refresh response received:", refreshResponse.data);
        const newAccessToken = refreshResponse.data?.access_token;

        if (!newAccessToken) {
          console.error("Missing access token in refresh response:", refreshResponse.data);
          throw new Error("Missing access token in refresh response");
        }

        // Update ONLY the access token in Redux
        store.dispatch(updateAccessToken(newAccessToken));
        console.log("Access token refreshed successfully");

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
