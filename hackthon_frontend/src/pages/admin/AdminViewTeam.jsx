import React, { useState, useEffect } from "react";
import { Users, UserPlus, ArrowLeft, Shield, Eye, EyeOff, Clock, Calendar } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getTeamsManagementRoute, toggleTeamStatusRoute } from "../../services/userService";
import { toast } from "react-toastify";
import Sidebar from "../../components/Sidebar";

export default function AdminViewTeam() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Fetch teams data on component mount
  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setLoading(true);
        const response = await getTeamsManagementRoute();
        
        if (response.status === 200) {
          setTeams(response.data.teams || []);
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

    fetchTeams();
  }, []);

  const handleToggleTeamStatus = async (teamId, currentStatus) => {
    try {
      const response = await toggleTeamStatusRoute(teamId);
      
      if (response.status === 200) {
        // Update the local state
        setTeams(prevTeams => 
          prevTeams.map(team => 
            team.id === teamId 
              ? { ...team, is_active: !team.is_active }
              : team
          )
        );
        
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

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span className="text-white text-lg">Loading teams...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex overflow-hidden">
      <div className="absolute top-0 left-0 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '700ms'}}></div>
      <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '1000ms'}}></div>

      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:100px_100px]"></div>
      <Sidebar isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />
      
      <div className="flex-1 relative z-10 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-8">
          <button onClick={() => navigate("/admin_home_page")} className="flex items-center gap-2 text-purple-300 hover:text-purple-200 transition-colors mb-8 group">
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back to Dashboard</span>
          </button>

          <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl p-8 border border-white/20 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>

            <div className="relative z-10">
              <div className="flex items-center gap-4 mb-8">
                <div className="p-4 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl shadow-lg shadow-purple-500/50">
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
                <div className="grid gap-6">
                  {teams.map((team) => (
                    <div
                      key={team.id}
                      className={`backdrop-blur-xl rounded-2xl p-6 border transition-all duration-300 ${
                        team.is_active 
                          ? 'bg-white/10 border-green-500/30' 
                          : 'bg-white/5 border-red-500/30'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-4">
                            <div className={`p-3 rounded-xl ${
                              team.is_active ? 'bg-gradient-to-br from-green-500 to-emerald-500' : 'bg-gradient-to-br from-red-500 to-pink-500'
                            }`}>
                              <Users className="w-6 h-6 text-white" />
                            </div>
                            <div>
                              <h3 className="text-2xl font-bold text-white">{team.name}</h3>
                              <p className="text-gray-300">Created on {formatDate(team.created_at)}</p>
                            </div>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                            <div className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10">
                              <div className="flex items-center gap-3">
                                <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-lg">
                                  <Users className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                  <p className="text-xs text-gray-400">Total</p>
                                  <p className="text-white font-semibold">{team.member_count} Members</p>
                                </div>
                              </div>
                            </div>

                            <div className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10">
                              <div className="flex items-center gap-3">
                                <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg">
                                  <Shield className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                  <p className="text-xs text-gray-400">Active</p>
                                  <p className="text-white font-semibold">{team.active_member_count} Members</p>
                                </div>
                              </div>
                            </div>

                            <div className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10">
                              <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${
                                  team.is_active ? 'bg-gradient-to-br from-green-500 to-emerald-500' : 'bg-gradient-to-br from-red-500 to-pink-500'
                                }`}>
                                  {team.is_active ? <Eye className="w-5 h-5 text-white" /> : <EyeOff className="w-5 h-5 text-white" />}
                                </div>
                                <div>
                                  <p className="text-xs text-gray-400">Status</p>
                                  <p className={`font-semibold ${team.is_active ? 'text-green-300' : 'text-red-300'}`}>
                                    {team.is_active ? 'Active' : 'Inactive'}
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="flex flex-col gap-3 ml-6">
                          <button
                            onClick={() => handleAddMember(team.id)}
                            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 via-purple-500 to-blue-500 hover:from-purple-500 hover:via-purple-400 hover:to-blue-400 text-white py-3 px-6 rounded-xl font-semibold shadow-lg hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-purple-500/50 transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
                          >
                            <UserPlus className="w-5 h-5" />
                            Add Member
                          </button>

                          <button
                            onClick={() => handleToggleTeamStatus(team.id, team.is_active)}
                            className={`flex items-center gap-2 py-3 px-6 rounded-xl font-semibold shadow-lg hover:shadow-xl focus:outline-none focus:ring-4 transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 ${
                              team.is_active
                                ? 'bg-gradient-to-r from-red-600 via-red-500 to-pink-500 hover:from-red-500 hover:via-red-400 hover:to-pink-400 focus:ring-red-500/50 text-white'
                                : 'bg-gradient-to-r from-green-600 via-green-500 to-emerald-500 hover:from-green-500 hover:via-green-400 hover:to-emerald-400 focus:ring-green-500/50 text-white'
                            }`}
                          >
                            {team.is_active ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            {team.is_active ? 'Block Team' : 'Unblock Team'}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
