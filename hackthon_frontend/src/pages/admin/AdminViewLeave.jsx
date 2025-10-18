import React, { useState, useEffect } from "react";
import { Calendar, Clock, User, ArrowLeft, CheckCircle, XCircle, Filter, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getLeaveRequestsRoute, approveRejectLeaveRequestRoute } from "../../services/userService";
import { toast } from "react-toastify";
import Sidebar from "../../components/Sidebar";

export default function AdminViewLeave() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [leaveRequests, setLeaveRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState('pending');
    const [pagination, setPagination] = useState({
        currentPage: 1,
        totalPages: 1,
        totalCount: 0,
        pageSize: 10,
        hasNext: false,
        hasPrevious: false,
    });
    const [actionLoading, setActionLoading] = useState({});
    const navigate = useNavigate();

    // Fetch leave requests data
    const fetchLeaveRequests = async (page = 1, pageSize = 10, status = 'pending') => {
        try {
            setLoading(true);
            const response = await getLeaveRequestsRoute(page, pageSize, status);
            
            if (response.status === 200) {
                setLeaveRequests(response.data.leave_requests || []);
                setPagination(response.data.pagination || {
                    currentPage: 1,
                    totalPages: 1,
                    totalCount: 0,
                    pageSize: 10,
                    hasNext: false,
                    hasPrevious: false,
                });
            }
        } catch (error) {
            console.error("Error fetching leave requests:", error);
            toast.error("Failed to load leave requests", {
                position: "bottom-center",
            });
        } finally {
            setLoading(false);
        }
    };

    // Fetch leave requests on component mount and when filters change
    useEffect(() => {
        fetchLeaveRequests(pagination.currentPage, pagination.pageSize, statusFilter);
    }, [statusFilter]);

    const handlePageChange = (newPage) => {
        fetchLeaveRequests(newPage, pagination.pageSize, statusFilter);
    };

    const handleStatusFilterChange = (newStatus) => {
        setStatusFilter(newStatus);
        setPagination(prev => ({ ...prev, currentPage: 1 }));
    };

    const handleApproveReject = async (leaveRequestId, action) => {
        try {
            setActionLoading(prev => ({ ...prev, [leaveRequestId]: true }));
            
            const response = await approveRejectLeaveRequestRoute(leaveRequestId, action);
            
            if (response.status === 200) {
                const actionText = action === 'approve' ? 'approved' : 'rejected';
                toast.success(`Leave request ${actionText} successfully`, {
                    position: "bottom-center",
                });
                
                // Refresh the data
                await fetchLeaveRequests(pagination.currentPage, pagination.pageSize, statusFilter);
            }
        } catch (error) {
            console.error(`Error ${action}ing leave request:`, error);
            const errorMessage = error.response?.data?.error?.commonError || `Failed to ${action} leave request`;
            toast.error(errorMessage, {
                position: "bottom-center",
            });
        } finally {
            setActionLoading(prev => ({ ...prev, [leaveRequestId]: false }));
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'pending': return 'text-yellow-600 bg-yellow-100';
            case 'approved': return 'text-green-600 bg-green-100';
            case 'rejected': return 'text-red-600 bg-red-100';
            default: return 'text-gray-600 bg-gray-100';
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    const formatDateTime = (dateString) => {
        return new Date(dateString).toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (loading && leaveRequests.length === 0) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex items-center justify-center">
                <div className="text-white text-xl">Loading leave requests...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex overflow-hidden">
            {/* Background effects */}
            <div className="absolute top-0 left-0 w-96 h-96 bg-gray-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
            <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '700ms'}}></div>
            <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '1000ms'}}></div>

            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:100px_100px]"></div>

            {/* Sidebar */}
            <Sidebar 
                isSidebarOpen={isSidebarOpen}
                setIsSidebarOpen={setIsSidebarOpen}
            />

            {/* Main Content */}
            <div className="flex-1 relative z-10 overflow-y-auto">
                {/* Header */}
                <div className="bg-black/20 backdrop-blur-xl border-b border-white/10 p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => navigate("/admin/dashboard")}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-white"
                            >
                                <ArrowLeft className="w-4 h-4" />
                                Back to Dashboard
                            </button>
                            <h1 className="text-2xl font-bold text-white">Leave Requests Management</h1>
                        </div>

                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => fetchLeaveRequests(pagination.currentPage, pagination.pageSize, statusFilter)}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 transition-all text-white"
                            >
                                <RefreshCw className="w-4 h-4" />
                                Refresh
                            </button>
                        </div>
                    </div>
                </div>

                <div className="p-6">
                    <div className="max-w-7xl mx-auto">
                        {/* Filters */}
                        <div className="mb-6 flex items-center gap-4">
                            <div className="flex items-center gap-2 text-white">
                                <Filter className="w-4 h-4" />
                                <span>Status:</span>
                            </div>
                            <div className="flex gap-2">
                                {['pending', 'approved', 'rejected', 'all'].map(status => (
                                    <button
                                        key={status}
                                        onClick={() => handleStatusFilterChange(status)}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                                            statusFilter === status
                                                ? 'bg-blue-600 text-white'
                                                : 'bg-white/10 text-white/70 hover:bg-white/20'
                                        }`}
                                    >
                                        {status.charAt(0).toUpperCase() + status.slice(1)}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Leave Requests Table */}
                        <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead className="bg-white/5 border-b border-white/20">
                                        <tr>
                                            <th className="px-6 py-4 text-left text-white/80 font-medium">User</th>
                                            <th className="px-6 py-4 text-left text-white/80 font-medium">Team</th>
                                            <th className="px-6 py-4 text-left text-white/80 font-medium">Date</th>
                                            <th className="px-6 py-4 text-left text-white/80 font-medium">Reason</th>
                                            <th className="px-6 py-4 text-left text-white/80 font-medium">Slots</th>
                                            <th className="px-6 py-4 text-left text-white/80 font-medium">Status</th>
                                            <th className="px-6 py-4 text-left text-white/80 font-medium">Requested</th>
                                            {statusFilter === 'pending' && (
                                                <th className="px-6 py-4 text-center text-white/80 font-medium">Actions</th>
                                            )}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/10">
                                        {leaveRequests.map((request) => (
                                            <tr key={request.id} className="hover:bg-white/5 transition-colors">
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                                                            {request.user.name.charAt(0).toUpperCase()}
                                                        </div>
                                                        <div>
                                                            <div className="text-white font-medium">{request.user.name}</div>
                                                            <div className="text-white/60 text-sm">{request.user.email}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 text-white">{request.team.name}</td>
                                                <td className="px-6 py-4 text-white">{formatDate(request.date)}</td>
                                                <td className="px-6 py-4 text-white/80">{request.reason}</td>
                                                <td className="px-6 py-4 text-white/80">{request.slots_count} slots</td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                                                        {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-white/60 text-sm">
                                                    {formatDateTime(request.requested_at)}
                                                </td>
                                                {statusFilter === 'pending' && (
                                                    <td className="px-6 py-4">
                                                        <div className="flex items-center justify-center gap-2">
                                                            <button
                                                                onClick={() => handleApproveReject(request.id, 'approve')}
                                                                disabled={actionLoading[request.id]}
                                                                className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-green-600/50 text-white rounded-lg text-sm transition-all"
                                                            >
                                                                <CheckCircle className="w-4 h-4" />
                                                                Approve
                                                            </button>
                                                            <button
                                                                onClick={() => handleApproveReject(request.id, 'reject')}
                                                                disabled={actionLoading[request.id]}
                                                                className="flex items-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 disabled:bg-red-600/50 text-white rounded-lg text-sm transition-all"
                                                            >
                                                                <XCircle className="w-4 h-4" />
                                                                Reject
                                                            </button>
                                                        </div>
                                                    </td>
                                                )}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {leaveRequests.length === 0 && (
                                <div className="text-center py-12 text-white/60">
                                    <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    <p>No leave requests found</p>
                                </div>
                            )}
                        </div>

                        {/* Pagination */}
                        {pagination.totalPages > 1 && (
                            <div className="mt-6 flex items-center justify-between text-white">
                                <div className="text-sm">
                                    Showing {((pagination.currentPage - 1) * pagination.pageSize) + 1} to {Math.min(pagination.currentPage * pagination.pageSize, pagination.totalCount)} of {pagination.totalCount} results
                                </div>
                                
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => handlePageChange(1)}
                                        disabled={!pagination.hasPrevious}
                                        className="px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:bg-white/5 disabled:text-white/40 text-white transition-all"
                                    >
                                        First
                                    </button>
                                    <button
                                        onClick={() => handlePageChange(pagination.currentPage - 1)}
                                        disabled={!pagination.hasPrevious}
                                        className="px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:bg-white/5 disabled:text-white/40 text-white transition-all"
                                    >
                                        Previous
                                    </button>
                                    
                                    <span className="px-4 py-2 text-white">
                                        Page {pagination.currentPage} of {pagination.totalPages}
                                    </span>
                                    
                                    <button
                                        onClick={() => handlePageChange(pagination.currentPage + 1)}
                                        disabled={!pagination.hasNext}
                                        className="px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:bg-white/5 disabled:text-white/40 text-white transition-all"
                                    >
                                        Next
                                    </button>
                                    <button
                                        onClick={() => handlePageChange(pagination.totalPages)}
                                        disabled={!pagination.hasNext}
                                        className="px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:bg-white/5 disabled:text-white/40 text-white transition-all"
                                    >
                                        Last
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
