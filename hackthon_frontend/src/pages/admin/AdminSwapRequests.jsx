import React, { useState, useEffect } from "react";
import { ArrowLeft, Clock, User, Calendar, X, RefreshCw, RotateCcw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getAdminSwapRequestsRoute, adminRejectSwapRequestRoute } from "../../services/userService";
import { toast } from "react-toastify";
import Sidebar from "../../components/Sidebar";
import Pagination from "../../components/Pagination";

export default function AdminSwapRequests() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [loading, setLoading] = useState(true);
    const [swapRequests, setSwapRequests] = useState([]);
    const [processingId, setProcessingId] = useState(null);
    const navigate = useNavigate();
    
    // Pagination state
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [pageSize] = useState(10);

    const fetchSwapRequests = async (page = 1) => {
        try {
            setLoading(true);
            const response = await getAdminSwapRequestsRoute(page, pageSize);
            if (response.data) {
                setSwapRequests(response.data.swap_requests || []);
                
                // Update pagination state
                if (response.data.pagination) {
                    setCurrentPage(response.data.pagination.current_page);
                    setTotalPages(response.data.pagination.total_pages);
                    setTotalCount(response.data.pagination.total_count);
                }
            }
        } catch (error) {
            console.error("Error fetching swap requests:", error);
            toast.error("Failed to load swap requests");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSwapRequests(currentPage);
    }, [currentPage]);

    const handleRejectRequest = async (swapRequestId) => {
        try {
            setProcessingId(swapRequestId);
            const response = await adminRejectSwapRequestRoute(swapRequestId);

            if (response.data) {
                toast.success(response.data.message);
                await fetchSwapRequests(currentPage); // Refresh the list
            }
        } catch (error) {
            console.error("Error rejecting swap request:", error);
            const errorMessage = error.response?.data?.error?.commonError || "Failed to reject swap request";
            toast.error(errorMessage);
        } finally {
            setProcessingId(null);
        }
    };

    const handlePageChange = (page) => {
        setCurrentPage(page);
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

    if (loading && swapRequests.length === 0) {
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
                                onClick={() => navigate("/admin_home_page")}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-white"
                            >
                                <ArrowLeft className="w-4 h-4" />
                                Back to Dashboard
                            </button>
                        </div>

                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => fetchSwapRequests(currentPage)}
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
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-3 bg-blue-600/20 rounded-xl">
                                    <RotateCcw className="w-8 h-8 text-blue-400" />
                                </div>
                                <div>
                                    <h1 className="text-3xl font-bold text-white mb-2">Admin - Swap Requests</h1>
                                    <p className="text-gray-300">
                                        Review and manage slot swap requests across all teams.
                                    </p>
                                    {totalCount > 0 && (
                                        <p className="text-blue-400 text-sm mt-1">
                                            {totalCount} pending swap request{totalCount !== 1 ? 's' : ''}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Swap Requests List */}
                        {swapRequests.length > 0 ? (
                            <div className="space-y-4">
                                {swapRequests.map((request) => (
                                    <div key={request.id} className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-4 mb-6">
                                                    <div className="p-3 bg-blue-600/20 rounded-xl">
                                                        <RotateCcw className="w-6 h-6 text-blue-400" />
                                                    </div>
                                                    <div>
                                                        <h3 className="text-xl font-semibold text-white">
                                                            {request.from_member.name} wants to swap with {request.to_member.name}
                                                        </h3>
                                                        <p className="text-gray-400">
                                                            {request.from_member.email} ↔ {request.to_member.email}
                                                        </p>
                                                    </div>
                                                </div>

                                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                                    {/* From Slot Details */}
                                                    <div className="bg-white/5 rounded-xl p-4">
                                                        <h4 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
                                                            <User className="w-5 h-5" />
                                                            {request.from_member.name}'s Current Slot
                                                        </h4>
                                                        <div className="space-y-2 text-sm">
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Team:</span>
                                                                <span className="text-white">{request.from_slot.team_name}</span>
                                                            </div>
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Date:</span>
                                                                <span className="text-white">{formatDate(request.from_slot.date)}</span>
                                                            </div>
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Time:</span>
                                                                <span className="text-white">
                                                                    {formatTime(request.from_slot.start_time)} - {formatTime(request.from_slot.end_time)}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* To Slot Details */}
                                                    <div className="bg-white/5 rounded-xl p-4">
                                                        <h4 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
                                                            <User className="w-5 h-5" />
                                                            {request.to_member.name}'s Slot (Wants to swap to)
                                                        </h4>
                                                        <div className="space-y-2 text-sm">
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Team:</span>
                                                                <span className="text-white">{request.to_slot.team_name}</span>
                                                            </div>
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Date:</span>
                                                                <span className="text-white">{formatDate(request.to_slot.date)}</span>
                                                            </div>
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-400">Time:</span>
                                                                <span className="text-white">
                                                                    {formatTime(request.to_slot.start_time)} - {formatTime(request.to_slot.end_time)}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Request Info */}
                                                <div className="mt-4 bg-white/5 rounded-xl p-4">
                                                    <div className="flex justify-between items-center">
                                                        <div>
                                                            <span className="text-gray-400 text-sm">Requested:</span>
                                                            <span className="text-white ml-2">{formatDateTime(request.created_at)}</span>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-gray-400 text-sm">Status:</span>
                                                            <span className="text-yellow-400 font-medium">Pending</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Action Button - Only Reject */}
                                            <div className="flex gap-3 ml-6">
                                                <button
                                                    onClick={() => handleRejectRequest(request.id)}
                                                    disabled={processingId === request.id}
                                                    className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-600/50 text-white rounded-lg transition-all disabled:cursor-not-allowed"
                                                >
                                                    <X className="w-4 h-4" />
                                                    {processingId === request.id ? 'Processing...' : 'Reject'}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-16">
                                <div className="p-6 bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 max-w-md mx-auto">
                                    <RotateCcw className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                                    <h3 className="text-xl font-semibold text-white mb-2">No Swap Requests</h3>
                                    <p className="text-gray-400">
                                        There are no pending swap requests at the moment.
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div className="mt-8">
                                <Pagination
                                    currentPage={currentPage}
                                    totalPages={totalPages}
                                    totalCount={totalCount}
                                    pageSize={pageSize}
                                    onPageChange={handlePageChange}
                                />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
