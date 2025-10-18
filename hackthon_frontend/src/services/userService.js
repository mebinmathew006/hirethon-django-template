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

export const createTeamRoute = async (teamData) => {
    const response = await axiosInstance.post('/api/managers/create-team/', teamData);
    return response;
}

export const getTeamsListRoute = async () => {
    const response = await axiosInstance.get('/api/managers/teams-list/');
    return response;
}

export const getUsersListRoute = async () => {
    const response = await axiosInstance.get('/api/managers/users-list/');
    return response;
}

export const createTeamMemberRoute = async (teamMemberData) => {
    const response = await axiosInstance.post('/api/managers/create-team-member/', teamMemberData);
    return response;
}

export const getTeamsManagementRoute = async (page = 1, pageSize = 10) => {
    const response = await axiosInstance.get(`/api/managers/teams-management/?page=${page}&page_size=${pageSize}`);
    return response;
}

export const toggleTeamStatusRoute = async (teamId) => {
    const response = await axiosInstance.patch(`/api/managers/toggle-team-status/${teamId}/`);
    return response;
}

export const createTeamMemberForTeamRoute = async (teamId, teamMemberData) => {
    const response = await axiosInstance.post(`/api/managers/add-member-to-team/${teamId}/`, teamMemberData);
    return response;
}

export const getUsersManagementRoute = async (page = 1, pageSize = 10) => {
    const response = await axiosInstance.get(`/api/managers/users-management/?page=${page}&page_size=${pageSize}`);
    return response;
}

export const toggleUserStatusRoute = async (userId) => {
    const response = await axiosInstance.patch(`/api/managers/toggle-user-status/${userId}/`);
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