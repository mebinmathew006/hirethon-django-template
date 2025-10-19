import React, { useState, useEffect, useCallback } from "react";
import { Users, Clock, Calendar, User, Phone, Mail, RefreshCw, AlertCircle, Check } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getUserTeamsOncallRoute, getAllTeamsOncallRoute } from "../../services/userService";
import { toast } from "react-toastify";
import UserSidebar from "../../components/UserSidebar";
import Pagination from "../../components/Pagination";

export default function UserViewTeams() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [teamsData, setTeamsData] = useState([]);
  const [currentTime, setCurrentTime] = useState(null);
  const [showAllTeams, setShowAllTeams] = useState(true); // Default to showing all teams
  const [totalTeams, setTotalTeams] = useState(0);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize] = useState(10); // You can make this configurable if needed
  
  const navigate = useNavigate();

  // Fetch teams on-call data
  const fetchTeamsData = useCallback(async (showAll = true, page = 1) => {
    try {
      setLoading(true);
      const response = showAll ? 
        await getAllTeamsOncallRoute(page, pageSize) : 
        await getUserTeamsOncallRoute();
      
      if (response.status === 200) {
        setTeamsData(response.data.teams);
        setCurrentTime(response.data.current_time);
        setTotalTeams(response.data.total_teams || response.data.teams.length);
        
        // Handle pagination data for "All Teams" view
        if (showAll && response.data.pagination) {
          setCurrentPage(response.data.pagination.current_page);
          setTotalPages(response.data.pagination.total_pages);
          setTotalCount(response.data.pagination.total_count);
        } else {
          // For "My Teams" view, there's no pagination, so reset pagination state
          setCurrentPage(1);
          setTotalPages(1);
          setTotalCount(response.data.teams.length);
        }
      }
    } catch (error) {
      console.error("Error fetching teams data:", error);
      toast.error("Failed to load teams data", {
        position: "bottom-center",
      });
    } finally {
      setLoading(false);
    }
  }, [pageSize]);

  // Handle page change for pagination
  const handlePageChange = useCallback((page) => {
    setCurrentPage(page);
    if (showAllTeams) {
      fetchTeamsData(true, page);
    }
  }, [showAllTeams, fetchTeamsData]);

  // Handle view toggle (My Teams vs All Teams)
  const handleViewToggle = useCallback((showAll) => {
    setShowAllTeams(showAll);
    setCurrentPage(1); // Reset to first page when switching views
  }, []);

  useEffect(() => {
    fetchTeamsData(showAllTeams, showAllTeams ? currentPage : 1);
    
    // Set up auto-refresh every 30 seconds to keep current on-call info up to date
    const interval = setInterval(() => {
      setCurrentTime(new Date().toISOString());
    }, 30000);

    return () => clearInterval(interval);
  }, [showAllTeams, currentPage, fetchTeamsData]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const isCurrentlyOnCall = (slot) => {
    if (!slot || !currentTime) return false;
    const now = new Date(currentTime);
    const startTime = new Date(slot.start_time);
    const endTime = new Date(slot.end_time);
    return now >= startTime && now <= endTime;
  };

  const getTimeUntilEnd = (endTime) => {
    if (!endTime || !currentTime) return '';
    const now = new Date(currentTime);
    const end = new Date(endTime);
    const diffMs = end - now;
    
    if (diffMs <= 0) return 'Ended';
    
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m remaining`;
    } else {
      return `${minutes}m remaining`;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span className="text-white text-lg">Loading teams...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex overflow-hidden">
      <div className="absolute top-0 left-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '700ms'}}></div>
      <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-green-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '1000ms'}}></div>

      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:100px_100px]"></div>
      
      {/* Sidebar */}
      <UserSidebar 
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        activeTab="teams"
      />
      
      {/* Main Content */}
      <div className="flex-1 relative z-10 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-8">
          {/* Header */}
          <div className="mb-8 flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">
                {showAllTeams ? 'All Teams & On-Call Schedule' : 'My Teams & On-Call Schedule'}
              </h1>
              <p className="text-gray-300">
                {showAllTeams 
                  ? 'Current on-call personnel and schedule for all teams' 
                  : 'Current on-call personnel and upcoming schedule for your teams'
                }
                {totalTeams > 0 && (
                  <span className="ml-2 text-blue-400">({totalTeams} teams)</span>
                )}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {/* View Toggle */}
              <div className="backdrop-blur-xl bg-white/10 rounded-lg p-1 border border-white/20">
                <button
                  onClick={() => handleViewToggle(false)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    !showAllTeams 
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  My Teams
                </button>
                <button
                  onClick={() => handleViewToggle(true)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    showAllTeams 
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  All Teams
                </button>
              </div>
              
              <button
                onClick={() => fetchTeamsData(showAllTeams, currentPage)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>

          {/* Current Time */}
          {currentTime && (
            <div className="mb-8">
              <div className="backdrop-blur-xl bg-white/10 rounded-xl p-4 border border-white/20">
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-blue-400" />
                  <span className="text-gray-300">Current Time:</span>
                  <span className="text-white font-semibold">
                    {formatTime(currentTime)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Teams */}
          {teamsData && teamsData.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {teamsData.map((team) => (
                <div
                  key={team.id}
                  className="backdrop-blur-xl bg-white/10 rounded-3xl p-8 border border-white/20 shadow-2xl relative overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>
                  
                  <div className="relative z-10">
                    {/* Team Header */}
                    <div className="flex items-center gap-4 mb-6">
                      <div className={`p-4 rounded-2xl shadow-lg ${
                        team.is_user_member 
                          ? 'bg-gradient-to-br from-green-500 to-emerald-500 shadow-green-500/50' 
                          : 'bg-gradient-to-br from-blue-500 to-purple-500 shadow-blue-500/50'
                      }`}>
                        <Users className="w-8 h-8 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-2xl font-bold text-white">{team.name}</h3>
                          {team.is_user_member && (
                            <div className="flex items-center gap-1 px-3 py-1 bg-green-500/20 border border-green-500/30 rounded-full">
                              <Check className="w-4 h-4 text-green-400" />
                              <span className="text-green-400 text-sm font-medium">Member</span>
                            </div>
                          )}
                        </div>
                        <p className="text-gray-300">{team.member_count} members</p>
                      </div>
                    </div>

                    {/* Current On-Call */}
                    <div className="mb-6">
                      <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Phone className="w-5 h-5 text-green-400" />
                        Current On-Call
                      </h4>
                      
                      {team.current_oncall ? (
                        <div className="backdrop-blur-xl bg-green-500/20 rounded-xl p-6 border border-green-500/30">
                          <div className="flex items-center gap-4">
                            <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl">
                              <User className="w-6 h-6 text-white" />
                            </div>
                            <div className="flex-1">
                              <h5 className="text-lg font-semibold text-white">{team.current_oncall.name}</h5>
                              <p className="text-gray-300 flex items-center gap-2">
                                <Mail className="w-4 h-4" />
                                {team.current_oncall.email}
                              </p>
                              <p className="text-sm text-green-400 mt-2">
                                {formatTime(team.current_oncall.start_time)} - {formatTime(team.current_oncall.end_time)}
                              </p>
                              <p className="text-xs text-gray-400">
                                {getTimeUntilEnd(team.current_oncall.end_time)}
                              </p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="backdrop-blur-xl bg-red-500/20 rounded-xl p-6 border border-red-500/30">
                          <div className="flex items-center gap-4">
                            <AlertCircle className="w-6 h-6 text-red-400" />
                            <div>
                              <p className="text-red-400 font-semibold">No one currently on-call</p>
                              <p className="text-gray-300 text-sm">No active slot found for this team</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Upcoming Slots */}
                    {team.upcoming_slots && team.upcoming_slots.length > 0 && (
                      <div className="mb-6">
                        <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                          <Calendar className="w-5 h-5 text-blue-400" />
                          Upcoming Schedule
                        </h4>
                        
                        <div className="space-y-3">
                          {team.upcoming_slots.map((slot, index) => (
                            <div
                              key={index}
                              className="backdrop-blur-xl bg-white/5 rounded-lg p-4 border border-white/10"
                            >
                              <div className="flex justify-between items-start">
                                <div>
                                  <p className="text-white font-semibold">{slot.name}</p>
                                  <p className="text-gray-300 text-sm">{slot.email}</p>
                                </div>
                                <div className="text-right">
                                  <p className="text-blue-400 text-sm font-semibold">
                                    {formatTime(slot.start_time)} - {formatTime(slot.end_time)}
                                  </p>
                                  <p className="text-gray-400 text-xs">{formatDate(slot.date)}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Team Constraints */}
                    {team.team_schedule_constraints && (
                      <div className="border-t border-white/20 pt-6">
                        <h4 className="text-lg font-semibold text-white mb-4">Team Schedule Rules</h4>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="text-center">
                            <p className="text-gray-400 text-sm">Max Hours/Day</p>
                            <p className="text-white font-semibold">{team.team_schedule_constraints.max_hours_per_day}h</p>
                          </div>
                          <div className="text-center">
                            <p className="text-gray-400 text-sm">Max Hours/Week</p>
                            <p className="text-white font-semibold">{team.team_schedule_constraints.max_hours_per_week}h</p>
                          </div>
                          <div className="text-center">
                            <p className="text-gray-400 text-sm">Min Rest Hours</p>
                            <p className="text-white font-semibold">{team.team_schedule_constraints.min_rest_hours}h</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="p-4 bg-white/10 rounded-full w-20 h-20 mx-auto mb-4 flex items-center justify-center">
                <Users className="w-10 h-10 text-gray-400" />
              </div>
              <h4 className="text-xl text-gray-300 mb-2">No Teams Found</h4>
              <p className="text-gray-400">
                {showAllTeams 
                  ? 'No active teams found in the system.' 
                  : 'You are not currently assigned to any active teams.'
                }
              </p>
            </div>
          )}
          
          {/* Pagination - Only show for "All Teams" view */}
          {showAllTeams && totalPages > 1 && (
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
  );
}
