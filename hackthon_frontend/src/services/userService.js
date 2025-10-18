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

export const getUserDashboardRoute = async () => {
    const response = await axiosInstance.get('/api/members/dashboard/');
    return response;
}

export const logoutRoute = async () => {
    const response = await axiosInstance.post('/api/auth/logout/');
    return response;
}
export const getUserDetailsRoute = async () => {
    const response = await axios.get('/api/user/')
    return response.data
}

// Schedule-related API calls
export const getUserScheduleRoute = async () => {
    const response = await axiosInstance.get('/api/members/schedule/');
    return response;
}

export const getDaySlotsRoute = async (year, month, day) => {
    const response = await axiosInstance.get(`/api/members/day-slots/${year}/${month}/${day}/`);
    return response;
}

export const requestLeaveRoute = async (date, reason = 'Leave requested') => {
    const response = await axiosInstance.post('/api/members/request-leave/', {
        date: date,
        reason: reason
    });
    return response;
}

export const requestSwapRoute = async (slotId, toMemberId) => {
    const response = await axiosInstance.post('/api/members/request-swap/', {
        slot_id: slotId,
        to_member_id: toMemberId
    });
    return response;
}

export const getSwapRequestsRoute = async () => {
    const response = await axiosInstance.get('/api/members/swap-requests/');
    return response;
}

export const respondToSwapRequestRoute = async (swapRequestId, action) => {
    const response = await axiosInstance.post(`/api/members/swap-requests/${swapRequestId}/respond/`, {
        action: action
    });
    return response;
}