import React, { useState, useEffect } from "react";
import { ArrowLeft, Clock, User, Calendar, Check, X, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getSwapRequestsRoute, respondToSwapRequestRoute, getUserDashboardRoute } from "../../services/userService";
import { toast } from "react-toastify";
import UserSidebar from "../../components/UserSidebar";
export default function SwapRequests() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [loading, setLoading] = useState(true);
    const [swapRequests, setSwapRequests] = useState([]);
    const [processingId, setProcessingId] = useState(null);
    const [userData, setUserData] = useState(null);
    const navigate = useNavigate();

    const fetchUserData = async () => {
        try {
            const response = await getUserDashboardRoute();
            if (response.status === 200) {
                setUserData(response.data.user);
            }
        } catch (error) {
            console.error("Error fetching user data:", error);
        }
    };

    const fetchSwapRequests = async () => {
        try {
            setLoading(true);
            const response = await getSwapRequestsRoute();
            if (response.data) {
                setSwapRequests(response.data.swap_requests || []);
            }
        } catch (error) {
            console.error("Error fetching swap requests:", error);
            toast.error("Failed to load swap requests");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUserData();
        fetchSwapRequests();
    }, []);

    const handleRespondToRequest = async (swapRequestId, action) => {
        try {
            setProcessingId(swapRequestId);
            const response = await respondToSwapRequestRoute(swapRequestId, action);

            if (response.data) {
                toast.success(response.data.message);
                await fetchSwapRequests(); // Refresh the list
            }
        } catch (error) {
            console.error(`Error ${action}ing swap request:`, error);
            const errorMessage = error.response?.data?.error?.commonError || `Failed to ${action} swap request`;
            toast.error(errorMessage);
        } finally {
            setProcessingId(null);
        }
    };

    const formatDateTime = (dateTimeString) => {
        const date = new Date(dateTimeString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    };

    const formatTime = (dateTimeString) => {
        const date = new Date(dateTimeString);
        return date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex items-center justify-center">
                <div className="text-white text-xl">Loading swap requests...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex overflow-hidden">
            {/* Background effects */}
            <div className="absolute top-0 left-0 w-96 h-96 bg-grey-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
            <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '700ms' }}></div>
            <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '1000ms' }}></div>

            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:100px_100px]"></div>

            {/* Sidebar */}
            <UserSidebar
                isSidebarOpen={isSidebarOpen}
                setIsSidebarOpen={setIsSidebarOpen}
                userData={userData}
                activeTab="schedule"
            />

            {/* Main Content */}
            <div className="flex-1 relative z-10 overflow-y-auto">
                {/* Header */}
                <div className="bg-black/20 backdrop-blur-xl border-b border-white/10 p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => navigate("/user/schedule")}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-white"
                            >
                                <ArrowLeft className="w-4 h-4" />
                                Back to Schedule
                            </button>
                        </div>

                        <div className="flex items-center gap-4">
                            <button
                                onClick={fetchSwapRequests}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 transition-all text-white"
                            >
                                <RefreshCw className="w-4 h-4" />
                                Refresh
                            </button>
                        </div>
                    </div>
                </div>

                <div className="p-6">
                    <div className="max-w-6xl mx-auto">
                        {/* Header */}
                        <div className="mb-8">
                            <h1 className="text-3xl font-bold text-white mb-2">Swap Requests</h1>
                            <p className="text-gray-300">
                                Review and respond to slot swap requests from your team members.
                            </p>
                        </div>

                        {/* Swap Requests List */}
                        {swapRequests.length > 0 ? (
                            <div className="space-y-4">
                                {swapRequests.map((request) => (
                                    <div key={request.id} className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-4 mb-4">
                                                    <div className="p-3 bg-blue-600/20 rounded-xl">
                                                        <User className="w-6 h-6 text-blue-400" />
                                                    </div>
                                                    <div>
                                                        <h3 className="text-xl font-semibold text-white">
                                                            {request.from_member.name} wants to swap
                                                        </h3>
                                                        <p className="text-gray-400">{request.from_member.email}</p>
                                                    </div>
                                                </div>

                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                    {/* Slot Details */}
                                                    <div className="bg-white/5 rounded-xl p-4">
                                                        <h4 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
                                                            <Calendar className="w-5 h-5" />
                                                            Slot Details
                                                        </h4>
                                                        <div className="space-y-2 text-sm">
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Team:</span>
                                                                <span className="text-white">{request.slot.team_name}</span>
                                                            </div>
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Date:</span>
                                                                <span className="text-white">{formatDate(request.slot.date)}</span>
                                                            </div>
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Time:</span>
                                                                <span className="text-white">
                                                                    {formatTime(request.slot.start_time)} - {formatTime(request.slot.end_time)}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Request Info */}
                                                    <div className="bg-white/5 rounded-xl p-4">
                                                        <h4 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
                                                            <Clock className="w-5 h-5" />
                                                            Request Info
                                                        </h4>
                                                        <div className="space-y-2 text-sm">
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Requested:</span>
                                                                <span className="text-white">{formatDateTime(request.created_at)}</span>
                                                            </div>
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Status:</span>
                                                                <span className="text-yellow-400">Pending</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Action Buttons */}
                                            <div className="flex gap-3 ml-6">
                                                <button
                                                    onClick={() => handleRespondToRequest(request.id, 'approve')}
                                                    disabled={processingId === request.id}
                                                    className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-600/50 text-white rounded-lg transition-all disabled:cursor-not-allowed"
                                                >
                                                    <Check className="w-4 h-4" />
                                                    {processingId === request.id ? 'Processing...' : 'Approve'}
                                                </button>
                                                <button
                                                    onClick={() => handleRespondToRequest(request.id, 'reject')}
                                                    disabled={processingId === request.id}
                                                    className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-600/50 text-white rounded-lg transition-all disabled:cursor-not-allowed"
                                                >
                                                    <X className="w-4 h-4" />
                                                    Reject
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-16">
                                <div className="p-6 bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 max-w-md mx-auto">
                                    <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                                    <h3 className="text-xl font-semibold text-white mb-2">No Swap Requests</h3>
                                    <p className="text-gray-400">
                                        You don't have any pending swap requests at the moment.
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}