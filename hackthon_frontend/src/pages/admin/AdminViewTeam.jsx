import React, { useState, useEffect } from "react";
import { Users, UserPlus, ArrowLeft, Shield, Eye, EyeOff, Clock, Calendar, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, UserCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getTeamsManagementRoute, toggleTeamStatusRoute } from "../../services/userService";
import { toast } from "react-toastify";
import Sidebar from "../../components/Sidebar";

export default function AdminViewTeam() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalCount: 0,
    pageSize: 10,
    hasNext: false,
    hasPrevious: false,
  });
  const navigate = useNavigate();

  // Fetch teams data
  const fetchTeams = async (page = 1, pageSize = 10) => {
    try {
      setLoading(true);
      const response = await getTeamsManagementRoute(page, pageSize);
      
      if (response.status === 200) {
        setTeams(response.data.teams || []);
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
      console.error("Error fetching teams:", error);
      toast.error("Failed to load teams data", {
        position: "bottom-center",
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch teams data on component mount and when pagination changes
  useEffect(() => {
    fetchTeams(pagination.currentPage, pagination.pageSize);
  }, []);

  // Handle page change
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.totalPages && newPage !== pagination.currentPage) {
      fetchTeams(newPage, pagination.pageSize);
    }
  };

  const handleToggleTeamStatus = async (teamId, currentStatus) => {
    try {
      const response = await toggleTeamStatusRoute(teamId);
      
      if (response.status === 200) {
        // Refresh the current page to get updated data
        fetchTeams(pagination.currentPage, pagination.pageSize);
        
        toast.success(response.data.message, {
          position: "bottom-center",
        });
      }
    } catch (error) {
      console.error("Error toggling team status:", error);
      toast.error("Failed to toggle team status", {
        position: "bottom-center",
      });
    }
  };

  const handleAddMember = (teamId) => {
    navigate(`/add-team-member/${teamId}`);
  };

  const handleViewMembers = (teamId) => {
    navigate(`/view-team-members/${teamId}`);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
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
            <strong className="text-white">{totalCount}</strong> teams
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
          <span className="text-white text-lg">Loading teams...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex overflow-hidden">
      <div className="absolute top-0 left-0 w-96 h-96 bg-grey-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '700ms'}}></div>
      <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '1000ms'}}></div>

      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:100px_100px]"></div>
      <Sidebar isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />
      
      <div className="flex-1 relative z-10 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-8">
          <button onClick={() => navigate("/admin_home_page")} className="flex items-center gap-2 text-grey-300 hover:text-grey-200 transition-colors mb-8 group">
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back to Dashboard</span>
          </button>

          <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl p-8 border border-white/20 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>

            <div className="relative z-10">
              <div className="flex items-center gap-4 mb-8">
                <div className="p-4 bg-gradient-to-br from-grey-500 to-blue-500 rounded-2xl shadow-lg shadow-grey-500/50">
                  <Users className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold text-white">Team Management</h1>
                  <p className="text-gray-300 mt-1">Manage teams, members, and team status</p>
                </div>
              </div>

              {teams.length === 0 ? (
                <div className="text-center py-12">
                  <div className="p-4 bg-white/10 rounded-full w-20 h-20 mx-auto mb-4 flex items-center justify-center">
                    <Users className="w-10 h-10 text-gray-400" />
                  </div>
                  <h3 className="text-xl text-gray-300 mb-2">No Teams Found</h3>
                  <p className="text-gray-400">Create your first team to get started.</p>
                </div>
              ) : (
                <>
                  {/* Teams Table */}
                  <div className="backdrop-blur-xl bg-white/5 rounded-xl border border-white/10 overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-white/5 border-b border-white/10">
                          <tr>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-white">Team</th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-white">Created</th>
                            <th className="px-6 py-4 text-center text-sm font-semibold text-white">Total Members</th>
                            <th className="px-6 py-4 text-center text-sm font-semibold text-white">Active Members</th>
                            <th className="px-6 py-4 text-center text-sm font-semibold text-white">Status</th>
                            <th className="px-6 py-4 text-center text-sm font-semibold text-white">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {teams.map((team) => (
                            <tr
                              key={team.id}
                              className={`border-b border-white/5 transition-all duration-200 hover:bg-white/5 ${
                                team.is_active ? '' : 'opacity-75'
                              }`}
                            >
                              <td className="px-6 py-4">
                                <div className="flex items-center gap-3">
                                  <div className={`p-2 rounded-lg ${
                                    team.is_active ? 'bg-gradient-to-br from-green-500 to-emerald-500' : 'bg-gradient-to-br from-red-500 to-pink-500'
                                  }`}>
                                    <Users className="w-5 h-5 text-white" />
                                  </div>
                                  <div>
                                    <h3 className="text-lg font-semibold text-white">{team.name}</h3>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <p className="text-sm text-gray-300">{formatDate(team.created_at)}</p>
                              </td>
                              <td className="px-6 py-4 text-center">
                                <div className="flex items-center justify-center gap-2">
                                  <Users className="w-4 h-4 text-blue-400" />
                                  <span className="text-white font-semibold">{team.member_count}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 text-center">
                                <div className="flex items-center justify-center gap-2">
                                  <Shield className="w-4 h-4 text-green-400" />
                                  <span className="text-white font-semibold">{team.active_member_count}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 text-center">
                                <div className="flex items-center justify-center gap-2">
                                  {team.is_active ? (
                                    <>
                                      <Eye className="w-4 h-4 text-green-400" />
                                      <span className="text-green-300 font-semibold">Active</span>
                                    </>
                                  ) : (
                                    <>
                                      <EyeOff className="w-4 h-4 text-red-400" />
                                      <span className="text-red-300 font-semibold">Inactive</span>
                                    </>
                                  )}
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <div className="flex items-center justify-center gap-2 flex-wrap">
                                  <button
                                    onClick={() => handleViewMembers(team.id)}
                                    className="flex items-center gap-1 bg-gradient-to-r from-purple-600 to-indigo-500 hover:from-purple-500 hover:to-indigo-400 text-white py-2 px-4 rounded-lg text-sm font-medium shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all duration-200"
                                  >
                                    <UserCheck className="w-4 h-4" />
                                    View
                                  </button>
                                  <button
                                    onClick={() => handleAddMember(team.id)}
                                    className="flex items-center gap-1 bg-gradient-to-r from-grey-600 to-blue-500 hover:from-grey-500 hover:to-blue-400 text-white py-2 px-4 rounded-lg text-sm font-medium shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-grey-500/50 transition-all duration-200"
                                  >
                                    <UserPlus className="w-4 h-4" />
                                    Add
                                  </button>
                                  <button
                                    onClick={() => handleToggleTeamStatus(team.id, team.is_active)}
                                    className={`flex items-center gap-1 py-2 px-4 rounded-lg text-sm font-medium shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 transition-all duration-200 ${
                                      team.is_active
                                        ? 'bg-gradient-to-r from-red-600 to-pink-500 hover:from-red-500 hover:to-pink-400 focus:ring-red-500/50 text-white'
                                        : 'bg-gradient-to-r from-green-600 to-emerald-500 hover:from-green-500 hover:to-emerald-400 focus:ring-green-500/50 text-white'
                                    }`}
                                  >
                                    {team.is_active ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    {team.is_active ? 'Block' : 'Unblock'}
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
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
