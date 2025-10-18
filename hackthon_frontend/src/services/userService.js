import publicAxiosInstance from "../api/publicAxiosconfig";
import axiosInstance from "../api/axiosconfig";

export const loginRoute = async (email, password) => {
    const data = { email, password };
    const response = await publicAxiosInstance.post('/api/auth/login/', data)
    return response
}

export const createUserRoute = async (userData) => {
    const response = await axiosInstance.post('/api/managers/create-user/', userData);
    return response;
}

export const logoutRoute = async () => {
    const response = await axios.post('/api/logout/')
    return response.data
}
export const getUserDetailsRoute = async () => {
    const response = await axios.get('/api/user/')
    return response.data
}