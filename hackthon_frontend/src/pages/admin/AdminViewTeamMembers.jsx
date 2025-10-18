import React, { useState, useEffect } from "react";
import { ArrowLeft, Users, Clock, Calendar, User, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Shield } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { getTeamMembersWithScheduleRoute } from "../../services/userService";
import { toast } from "react-toastify";
import Sidebar from "../../components/Sidebar";

export default function AdminViewTeamMembers() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [members, setMembers] = useState([]);
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalCount: 0,
    pageSize: 10,
    hasNext: false,
    hasPrevious: false,
  });
  const [dateRange, setDateRange] = useState(null);
  const navigate = useNavigate();
  const { teamId } = useParams();

  // Fetch team members data
  const fetchMembers = async (page = 1, pageSize = 10) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getTeamMembersWithScheduleRoute(teamId, page, pageSize);
      
      if (response.status === 200) {
        setMembers(response.data.members || []);
        setTeam(response.data.team);
        setDateRange(response.data.date_range);
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
      console.error("Error fetching team members:", error);
      setError("Failed to load team members data");
      toast.error("Failed to load team members data", {
        position: "bottom-center",
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch members data on component mount and when pagination changes
  useEffect(() => {
    if (teamId) {
      fetchMembers(pagination.currentPage, pagination.pageSize);
    }
  }, [teamId]);

  // Handle page change
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.totalPages && newPage !== pagination.currentPage) {
      fetchMembers(newPage, pagination.pageSize);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatTime = (dateTimeString) => {
    return new Date(dateTimeString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const getDayOfWeek = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', { weekday: 'short' });
  };

  // Custom Pagination Component
  const CustomPagination = () => {
    const { currentPage, totalPages, totalCount, pageSize } = pagination;
    
    if (totalPages <= 1) return null;

    const getPageNumbers = () => {
      const pages = [];
      const maxButtons = 5;
      let startPage, endPage;

      if (totalPages <= maxButtons) {
        startPage = 1;
        endPage = totalPages;
      } else {
        const halfButtons = Math.floor(maxButtons / 2);
        if (currentPage <= halfButtons) {
          startPage = 1;
          endPage = maxButtons;
        } else if (currentPage + halfButtons >= totalPages) {
          startPage = totalPages - maxButtons + 1;
          endPage = totalPages;
        } else {
          startPage = currentPage - halfButtons;
          endPage = currentPage + halfButtons;
        }
      }

      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
      return pages;
    };

    const pageNumbers = getPageNumbers();
    const startItem = (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(currentPage * pageSize, totalCount);

    return (
      <div className="flex flex-col gap-4 mt-6">
        {/* Showing info */}
        <div className="text-sm text-gray-300 flex justify-between items-center">
          <span>
            Showing <strong className="text-white">{startItem}</strong> to <strong className="text-white">{endItem}</strong> of{" "}
            <strong className="text-white">{totalCount}</strong> members
          </span>
        </div>

        {/* Pagination buttons */}
        <div className="flex justify-center">
          <nav className="flex items-center gap-1">
            {/* First page */}
            <button
              onClick={() => handlePageChange(1)}
              disabled={currentPage === 1}
              className="p-2 rounded-lg bg-white/10 text-white hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <ChevronsLeft className="w-4 h-4" />
            </button>

            {/* Previous page */}
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={!pagination.hasPrevious}
              className="p-2 rounded-lg bg-white/10 text-white hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            {/* Page numbers */}
            {pageNumbers[0] > 1 && (
              <span className="px-3 py-2 text-gray-400">...</span>
            )}
            
            {pageNumbers.map((pageNum) => (
              <button
                key={pageNum}
                onClick={() => handlePageChange(pageNum)}
                className={`px-3 py-2 rounded-lg transition-all ${
                  pageNum === currentPage
                    ? 'bg-gradient-to-r from-grey-600 to-blue-500 text-white shadow-lg'
                    : 'bg-white/10 text-white hover:bg-white/20'
                }`}
              >
                {pageNum}
              </button>
            ))}

            {pageNumbers[pageNumbers.length - 1] < totalPages && (
              <span className="px-3 py-2 text-gray-400">...</span>
            )}

            {/* Next page */}
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={!pagination.hasNext}
              className="p-2 rounded-lg bg-white/10 text-white hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <ChevronRight className="w-4 h-4" />
            </button>

            {/* Last page */}
            <button
              onClick={() => handlePageChange(totalPages)}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg bg-white/10 text-white hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <ChevronsRight className="w-4 h-4" />
            </button>
          </nav>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span className="text-white text-lg">Loading team members...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-xl mb-4">Error</div>
          <div className="text-gray-300 mb-4">{error}</div>
          <button
            onClick={() => fetchMembers()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex overflow-hidden">
      <div className="absolute top-0 left-0 w-96 h-96 bg-gray-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '700ms'}}></div>
      <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '1000ms'}}></div>

      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:100px_100px]"></div>
      <Sidebar isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />
      
      <div className="flex-1 relative z-10 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-8">
          <button onClick={() => navigate("/view-teams")} className="flex items-center gap-2 text-gray-300 hover:text-gray-200 transition-colors mb-8 group">
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back to Teams</span>
          </button>

          <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl p-8 border border-white/20 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>

            <div className="relative z-10">
              <div className="flex items-center gap-4 mb-8">
                <div className="p-4 bg-gradient-to-br from-gray-500 to-blue-500 rounded-2xl shadow-lg shadow-gray-500/50">
                  <Users className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold text-white">{team?.name} Members</h1>
                  <p className="text-gray-300 mt-1">
                    {dateRange && (
                      <>Schedule for {formatDate(dateRange.start_date)} - {formatDate(dateRange.end_date)}</>
                    )}
                  </p>
                </div>
              </div>

              {members.length === 0 ? (
                <div className="text-center py-12">
                  <div className="p-4 bg-white/10 rounded-full w-20 h-20 mx-auto mb-4 flex items-center justify-center">
                    <Users className="w-10 h-10 text-gray-400" />
                  </div>
                  <h3 className="text-xl text-gray-300 mb-2">No Members Found</h3>
                  <p className="text-gray-400">This team doesn't have any active members yet.</p>
                </div>
              ) : (
                <>
                  {/* Members List */}
                  <div className="space-y-6">
                    {members.map((member) => (
                      <div
                        key={member.id}
                        className="backdrop-blur-xl bg-white/5 rounded-xl border border-white/10 overflow-hidden"
                      >
                        {/* Member Header */}
                        <div className="p-6 border-b border-white/10 bg-white/5">
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                              {member.name.charAt(0).toUpperCase()}
                            </div>
                            <div className="flex-1">
                              <h3 className="text-xl font-semibold text-white">{member.name}</h3>
                              <p className="text-gray-400">{member.email}</p>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="flex items-center gap-2">
                                <Shield className={`w-4 h-4 ${member.is_active ? 'text-green-400' : 'text-red-400'}`} />
                                <span className={`text-sm ${member.is_active ? 'text-green-300' : 'text-red-300'}`}>
                                  {member.is_active ? 'Active' : 'Inactive'}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4 text-blue-400" />
                                <span className="text-white font-medium">{member.total_slots} slots</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Schedule Grid */}
                        <div className="p-6">
                          <div className="grid grid-cols-7 gap-4">
                            {member.availability.map((day, index) => {
                              const daySlots = member.slots.filter(slot => slot.date === day.date);
                              const isAvailable = day.is_available;
                              
                              return (
                                <div key={day.date} className="min-h-[120px]">
                                  <div className="text-center mb-2">
                                    <div className="text-sm font-medium text-white">
                                      {getDayOfWeek(day.date)}
                                    </div>
                                    <div className="text-xs text-gray-400">
                                      {formatDate(day.date)}
                                    </div>
                                  </div>
                                  
                                  <div className={`p-2 rounded-lg border ${
                                    isAvailable 
                                      ? 'bg-green-500/10 border-green-500/20' 
                                      : 'bg-red-500/10 border-red-500/20'
                                  }`}>
                                    <div className="text-xs text-center mb-2">
                                      <span className={isAvailable ? 'text-green-300' : 'text-red-300'}>
                                        {isAvailable ? 'Available' : 'Leave'}
                                      </span>
                                      {day.reason && (
                                        <div className="text-gray-400 text-xs mt-1">
                                          {day.reason}
                                        </div>
                                      )}
                                    </div>
                                    
                                    {daySlots.map((slot, slotIndex) => (
                                      <div
                                        key={slotIndex}
                                        className="mb-1 p-1 bg-blue-500/20 rounded text-xs text-center border border-blue-500/30"
                                      >
                                        <div className="text-blue-200 font-medium">
                                          {formatTime(slot.start_time)}
                                        </div>
                                        <div className="text-blue-300">
                                          {formatTime(slot.end_time)}
                                        </div>
                                        <div className="text-gray-400">
                                          {slot.duration_hours}h
                                        </div>
                                      </div>
                                    ))}
                                    
                                    {daySlots.length === 0 && isAvailable && (
                                      <div className="text-xs text-gray-500 text-center">
                                        No shifts
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Pagination */}
                  <CustomPagination />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
