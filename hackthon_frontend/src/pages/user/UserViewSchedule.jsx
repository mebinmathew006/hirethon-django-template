import React, { useState, useEffect } from "react";
import { Calendar, Clock, Users, User, ArrowLeft, Plus, RefreshCw, MessageSquare } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getUserScheduleRoute, getDaySlotsRoute, requestLeaveRoute, requestSwapRoute, getUserDashboardRoute } from "../../services/userService";
import { toast } from "react-toastify";
import UserSidebar from "../../components/UserSidebar";

export default function UserViewSchedule() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [loading, setLoading] = useState(true);
    const [scheduleData, setScheduleData] = useState(null);
    const [currentMonth, setCurrentMonth] = useState(new Date());
    const [selectedDate, setSelectedDate] = useState(null);
    const [daySlotsModalOpen, setDaySlotsModalOpen] = useState(false);
    const [daySlotsData, setDaySlotsData] = useState(null);
    const [daySlotsLoading, setDaySlotsLoading] = useState(false);
    const [leaveModalOpen, setLeaveModalOpen] = useState(false);
    const [swapModalOpen, setSwapModalOpen] = useState(false);
    const [selectedSlot, setSelectedSlot] = useState(null);
    const [leaveReason, setLeaveReason] = useState("");
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

    const fetchScheduleData = async () => {
        try {
            setLoading(true);
            const response = await getUserScheduleRoute();
            if (response.data) {
                setScheduleData(response.data);
            }
        } catch (error) {
            console.error("Error fetching schedule data:", error);
            toast.error("Failed to load schedule data");
        } finally {
            setLoading(false);
        }
    };

    const fetchDaySlots = async (date) => {
        try {
            setDaySlotsLoading(true);
            const response = await getDaySlotsRoute(date.getFullYear(), date.getMonth() + 1, date.getDate());
            if (response.data) {
                setDaySlotsData(response.data);
            }
        } catch (error) {
            console.error("Error fetching day slots:", error);
            toast.error("Failed to load day slots");
        } finally {
            setDaySlotsLoading(false);
        }
    };

    useEffect(() => {
        fetchUserData();
        fetchScheduleData();
    }, []);

    const handleDateClick = async (date) => {
        setSelectedDate(date);
        await fetchDaySlots(date);
        setDaySlotsModalOpen(true);
    };

    const handleRequestLeave = async () => {
        if (!selectedDate) return;

        try {
            const response = await requestLeaveRoute(
                selectedDate.toISOString().split('T')[0],
                leaveReason || "Leave requested"
            );
            
            if (response.data) {
                toast.success("Leave request submitted successfully. Please wait for admin approval.");
                setLeaveModalOpen(false);
                setLeaveReason("");
                await fetchScheduleData(); // Refresh schedule data
            }
        } catch (error) {
            console.error("Error requesting leave:", error);
            const errorMessage = error.response?.data?.error?.commonError || "Failed to submit leave request";
            toast.error(errorMessage);
        }
    };

    const handleRequestSwap = async (toMemberId) => {
        if (!selectedSlot) return;

        try {
            const response = await requestSwapRoute(selectedSlot.id, toMemberId);
            
            if (response.data) {
                toast.success("Swap request sent successfully");
                setSwapModalOpen(false);
                setSelectedSlot(null);
                await fetchDaySlots(selectedDate); // Refresh day slots
            }
        } catch (error) {
            console.error("Error requesting swap:", error);
            toast.error("Failed to send swap request");
        }
    };

    const openSwapModal = (slot) => {
        setSelectedSlot(slot);
        setSwapModalOpen(true);
    };

    const openLeaveModal = () => {
        setLeaveModalOpen(true);
    };

    const getDaysInMonth = (date) => {
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());
        
        const days = [];
        const current = new Date(startDate);
        
        for (let i = 0; i < 42; i++) {
            days.push(new Date(current));
            current.setDate(current.getDate() + 1);
        }
        
        return days;
    };

    const hasSlotsOnDate = (checkDate) => {
        if (!scheduleData?.slots) return false;
        return scheduleData.slots.some(slot => 
            new Date(slot.date).toDateString() === checkDate.toDateString()
        );
    };

    const isMySlot = (checkDate) => {
        if (!scheduleData?.slots) return false;
        return scheduleData.slots.some(slot => 
            new Date(slot.date).toDateString() === checkDate.toDateString() && slot.is_mine
        );
    };

    const isAvailableOnDate = (checkDate) => {
        // User is available by default, only check for leave dates (is_available: false)
        if (!scheduleData?.availability) return true;
        const avail = scheduleData.availability.find(a => 
            new Date(a.date).toDateString() === checkDate.toDateString()
        );
        // If no record exists, user is available; if record exists, check is_available flag
        return avail ? avail.is_available : true;
    };

    const isCurrentMonth = (checkDate) => {
        return checkDate.getMonth() === currentMonth.getMonth() &&
               checkDate.getFullYear() === currentMonth.getFullYear();
    };

    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex items-center justify-center">
                <div className="text-white text-xl">Loading schedule...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex overflow-hidden">
            {/* Background effects */}
            <div className="absolute top-0 left-0 w-96 h-96 bg-grey-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
            <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '700ms'}}></div>
            <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '1000ms'}}></div>

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
                                onClick={() => navigate("/user/home")}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-white"
                            >
                                <ArrowLeft className="w-4 h-4" />
                                Back to Dashboard
                            </button>
                        </div>

                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => navigate("/user/swap-requests")}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-grey-600 hover:bg-grey-700 transition-all text-white"
                            >
                                <MessageSquare className="w-4 h-4" />
                                Swap Requests
                            </button>
                            
                            <button
                                onClick={fetchScheduleData}
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
                        {/* Calendar Header */}
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))}
                                    className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-white"
                                >
                                    ←
                                </button>
                                
                                <h1 className="text-2xl font-bold text-white">
                                    {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
                                </h1>
                                
                                <button
                                    onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))}
                                    className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-white"
                                >
                                    →
                                </button>
                            </div>

                            <button
                                onClick={() => setCurrentMonth(new Date())}
                                className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-white"
                            >
                                Today
                            </button>
                        </div>

                        {/* Calendar */}
                        <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 overflow-hidden">
                            {/* Day Headers */}
                            <div className="grid grid-cols-7 border-b border-white/20">
                                {dayNames.map(day => (
                                    <div key={day} className="p-4 text-center text-white/60 font-medium border-r border-white/20 last:border-r-0">
                                        {day}
                                    </div>
                                ))}
                            </div>

                            {/* Calendar Grid */}
                            <div className="grid grid-cols-7">
                                {getDaysInMonth(currentMonth).map((date, index) => {
                                    const hasSlots = hasSlotsOnDate(date);
                                    const isMySlotDay = isMySlot(date);
                                    const isAvailable = isAvailableOnDate(date);
                                    const isCurrentMonthDay = isCurrentMonth(date);

                                    return (
                                        <button
                                            key={index}
                                            onClick={() => handleDateClick(date)}
                                            className={`
                                                relative p-4 h-20 border-r border-b border-white/20 last:border-r-0 
                                                hover:bg-white/10 transition-all text-left
                                                ${isCurrentMonthDay ? 'text-white' : 'text-white/40'}
                                                ${hasSlots ? 'bg-blue-500/20' : ''}
                                                ${isMySlotDay ? 'bg-green-500/20' : ''}
                                                ${!isAvailable ? 'bg-red-500/20' : ''}
                                            `}
                                        >
                                            <div className="text-sm font-medium">{date.getDate()}</div>
                                            <div className="flex gap-1 mt-1">
                                                {hasSlots && (
                                                    <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                                                )}
                                                {isMySlotDay && (
                                                    <div className="w-2 h-2 rounded-full bg-green-400"></div>
                                                )}
                                                {!isAvailable && (
                                                    <div className="w-2 h-2 rounded-full bg-red-400"></div>
                                                )}
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Legend */}
                        <div className="mt-6 flex flex-wrap gap-6 text-white/80 text-sm">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-blue-400"></div>
                                <span>Has slots</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-green-400"></div>
                                <span>My assigned slots</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-400"></div>
                                <span>Leave/Unavailable</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Day Slots Modal */}
            {daySlotsModalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
                        <div className="p-6 border-b border-gray-200">
                            <div className="flex items-center justify-between">
                                <h2 className="text-2xl font-bold text-gray-900">
                                    {selectedDate?.toLocaleDateString('en-US', { 
                                        weekday: 'long', 
                                        year: 'numeric', 
                                        month: 'long', 
                                        day: 'numeric' 
                                    })}
                                </h2>
                                <div className="flex gap-3">
                                    {selectedDate && isAvailableOnDate(selectedDate) && (
                                        <button
                                            onClick={openLeaveModal}
                                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all flex items-center gap-2"
                                        >
                                            <Plus className="w-4 h-4" />
                                            Request Leave
                                        </button>
                                    )}
                                    <button
                                        onClick={() => setDaySlotsModalOpen(false)}
                                        className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-all"
                                    >
                                        Close
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 overflow-y-auto max-h-96">
                            {daySlotsLoading ? (
                                <div className="text-center py-8">Loading...</div>
                            ) : daySlotsData?.slots?.length > 0 ? (
                                <div className="space-y-4">
                                    {daySlotsData.slots.map(slot => (
                                        <div key={slot.id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <div className="font-medium text-gray-900">
                                                        {slot.team_name}
                                                    </div>
                                                    <div className="text-sm text-gray-600 flex items-center gap-2">
                                                        <Clock className="w-4 h-4" />
                                                        {new Date(slot.start_time).toLocaleTimeString('en-US', {
                                                            hour: 'numeric',
                                                            minute: '2-digit',
                                                            hour12: true
                                                        })} - {new Date(slot.end_time).toLocaleTimeString('en-US', {
                                                            hour: 'numeric',
                                                            minute: '2-digit',
                                                            hour12: true
                                                        })}
                                                    </div>
                                                    {slot.assigned_member && (
                                                        <div className="text-sm text-gray-600 flex items-center gap-2 mt-1">
                                                            <User className="w-4 h-4" />
                                                            {slot.assigned_member.name}
                                                        </div>
                                                    )}
                                                </div>
                                                
                                                {slot.is_mine && (
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => openSwapModal(slot)}
                                                            className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all text-sm"
                                                        >
                                                            Request Swap
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-8 text-gray-500">
                                    No slots scheduled for this date.
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Leave Request Modal */}
            {leaveModalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-2xl max-w-md w-full">
                        <div className="p-6 border-b border-gray-200">
                            <h3 className="text-xl font-bold text-gray-900">Request Leave</h3>
                            <p className="text-gray-600 mt-1">
                                {selectedDate?.toLocaleDateString('en-US', { 
                                    weekday: 'long', 
                                    year: 'numeric', 
                                    month: 'long', 
                                    day: 'numeric' 
                                })}
                            </p>
                        </div>
                        
                        <div className="p-6">
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Reason (optional)
                                </label>
                                <input
                                    type="text"
                                    value={leaveReason}
                                    onChange={(e) => setLeaveReason(e.target.value)}
                                    placeholder="e.g., Personal leave, Sick leave"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            
                            <div className="flex gap-3">
                                <button
                                    onClick={handleRequestLeave}
                                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all"
                                >
                                    Request Leave
                                </button>
                                <button
                                    onClick={() => {
                                        setLeaveModalOpen(false);
                                        setLeaveReason("");
                                    }}
                                    className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-all"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Swap Request Modal */}
            {swapModalOpen && selectedSlot && daySlotsData?.team_members && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-2xl max-w-md w-full">
                        <div className="p-6 border-b border-gray-200">
                            <h3 className="text-xl font-bold text-gray-900">Request Swap</h3>
                            <p className="text-gray-600 mt-1">
                                Select a team member to swap with for this slot.
                            </p>
                        </div>
                        
                        <div className="p-6 max-h-80 overflow-y-auto">
                            <div className="space-y-2">
                                {daySlotsData.team_members.map(member => (
                                    <button
                                        key={member.id}
                                        onClick={() => handleRequestSwap(member.id)}
                                        className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all"
                                    >
                                        <div className="font-medium text-gray-900">{member.name}</div>
                                        <div className="text-sm text-gray-600">{member.email}</div>
                                    </button>
                                ))}
                            </div>
                            
                            {daySlotsData.team_members.length === 0 && (
                                <div className="text-center py-4 text-gray-500">
                                    No other team members available for swap.
                                </div>
                            )}
                        </div>
                        
                        <div className="p-6 border-t border-gray-200">
                            <button
                                onClick={() => {
                                    setSwapModalOpen(false);
                                    setSelectedSlot(null);
                                }}
                                className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-all"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}