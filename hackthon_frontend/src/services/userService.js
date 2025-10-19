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

export const getDaySlotsRoute = async (year, month, day, forTeamId = null, afterCurrentTime = false) => {
    let url = `/api/members/day-slots/${year}/${month}/${day}/`;
    const params = new URLSearchParams();
    
    if (forTeamId) {
        params.append('for_team_id', forTeamId);
    }
    if (afterCurrentTime) {
        params.append('after_current_time', 'true');
    }
    
    if (params.toString()) {
        url += `?${params.toString()}`;
    }
    
    const response = await axiosInstance.get(url);
    return response;
}

export const requestLeaveRoute = async (date, reason = 'Leave requested') => {
    const response = await axiosInstance.post('/api/members/request-leave/', {
        date: date,
        reason: reason
    });
    return response;
}

export const requestSwapRoute = async (fromSlotId, toSlotId) => {
    const requestData = {
        from_slot_id: fromSlotId,
        to_slot_id: toSlotId
    };
    console.log("requestSwapRoute - sending data:", requestData);
    
    const response = await axiosInstance.post('/api/members/request-swap/', requestData);
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

// Leave Request Management (Admin)
export const getLeaveRequestsRoute = async (page = 1, pageSize = 10, status = 'pending') => {
    const response = await axiosInstance.get(`/api/managers/leave-requests/?page=${page}&page_size=${pageSize}&status=${status}`);
    return response;
}

export const approveRejectLeaveRequestRoute = async (leaveRequestId, action) => {
    const response = await axiosInstance.post(`/api/managers/leave-requests/${leaveRequestId}/approve-reject/`, {
        action: action
    });
    return response;
}

// Slot Management (Admin)
export const getAvailableUsersForSlotRoute = async (slotId) => {
    const response = await axiosInstance.get(`/api/managers/slots/${slotId}/available-users/`);
    return response;
}

export const assignUserToSlotRoute = async (slotId, userId) => {
    const response = await axiosInstance.post(`/api/managers/slots/${slotId}/assign-user/`, {
        user_id: userId
    });
    return response;
}

// Team Members Schedule (Admin)
export const getTeamMembersWithScheduleRoute = async (teamId, page = 1, pageSize = 10) => {
    const response = await axiosInstance.get(`/api/managers/teams/${teamId}/members-schedule/?page=${page}&page_size=${pageSize}`);
    return response;
}

// Dashboard Statistics (Admin)
export const getDashboardStatsRoute = async () => {
    const response = await axiosInstance.get(`/api/managers/dashboard-stats/`);
    return response;
}

// User Teams On-Call View
export const getUserTeamsOncallRoute = async () => {
    const response = await axiosInstance.get(`/api/members/teams-oncall/`);
    return response;
}

// All Teams On-Call View
export const getAllTeamsOncallRoute = async (page = 1, pageSize = 10) => {
    const response = await axiosInstance.get(`/api/members/all-teams-oncall/?page=${page}&page_size=${pageSize}`);
    return response;
}

// Admin Swap Requests Management
export const getAdminSwapRequestsRoute = async (page = 1, pageSize = 10) => {
    const response = await axiosInstance.get(`/api/managers/swap-requests/?page=${page}&page_size=${pageSize}`);
    return response;
}

export const adminRejectSwapRequestRoute = async (swapRequestId) => {
    const response = await axiosInstance.post(`/api/managers/swap-requests/${swapRequestId}/reject/`);
    return response;
}