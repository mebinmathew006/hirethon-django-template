import React, { useState, useEffect } from "react";
import { Users, Calendar, Clock, User, Mail, Zap, TrendingUp } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getUserDashboardRoute } from "../../services/userService";
import { toast } from "react-toastify";
import UserSidebar from "../../components/UserSidebar";

export default function UserHomePage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [userData, setUserData] = useState(null);
  const navigate = useNavigate();

  // Fetch user dashboard data
  const fetchUserData = async () => {
    try {
      setLoading(true);
      const response = await getUserDashboardRoute();
      
      if (response.status === 200) {
        setUserData(response.data.user);
      }
    } catch (error) {
      console.error("Error fetching user data:", error);
      toast.error("Failed to load user data", {
        position: "bottom-center",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserData();
  }, []);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin':
        return 'from-red-500 to-pink-500';
      case 'manager':
        return 'from-purple-500 to-indigo-500';
      case 'doctor':
        return 'from-blue-500 to-cyan-500';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'admin':
        return 'Admin';
      case 'manager':
        return 'Manager';
      case 'doctor':
        return 'Doctor';
      default:
        return 'User';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span className="text-white text-lg">Loading dashboard...</span>
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
      
      {/* Sidebar */}
      <UserSidebar 
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        userData={userData}
        activeTab="dashboard"
      />
      
      {/* Main Content */}
      <div className="flex-1 relative z-10 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2">Welcome back, {userData?.name}!</h1>
            <p className="text-gray-300">Here's what's happening with your work schedule today.</p>
          </div>

          {userData && (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-300 text-sm">My Teams</p>
                      <p className="text-3xl font-bold text-white">{userData.teams.length}</p>
                    </div>
                    <div className="p-3 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl">
                      <Users className="w-6 h-6 text-white" />
                    </div>
                  </div>
                </div>

                <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-300 text-sm">Available Hours</p>
                      <p className="text-3xl font-bold text-white">{userData.total_availability_hours}h</p>
                    </div>
                    <div className="p-3 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl">
                      <Clock className="w-6 h-6 text-white" />
                    </div>
                  </div>
                </div>

                <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-300 text-sm">Max Hours/Day</p>
                      <p className="text-3xl font-bold text-white">{userData.max_hours_per_day}h</p>
                    </div>
                    <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl">
                      <TrendingUp className="w-6 h-6 text-white" />
                    </div>
                  </div>
                </div>

                <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-300 text-sm">Account Status</p>
                      <p className="text-xl font-bold text-green-400">Active</p>
                    </div>
                    <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl">
                      <Zap className="w-6 h-6 text-white" />
                    </div>
                  </div>
                </div>
              </div>

              {/* User Profile Card */}
              <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl p-8 border border-white/20 relative overflow-hidden mb-8">
                <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>
                
                <div className="relative z-10">
                  <div className="flex items-center gap-6 mb-6">
                    <div className={`p-4 rounded-2xl bg-gradient-to-br ${getRoleColor(userData.role)} shadow-lg`}>
                      <User className="w-8 h-8 text-white" />
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold text-white">{userData.name}</h2>
                      <p className="text-gray-300 flex items-center gap-2 mt-1">
                        <Mail className="w-4 h-4" />
                        {userData.email}
                      </p>
                      <p className="text-sm text-gray-400 capitalize mt-1">
                        {userData.role} • Joined {formatDate(userData.date_joined)}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4">Work Preferences</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Max Hours per Day</span>
                          <span className="text-white font-semibold">{userData.max_hours_per_day}h</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Max Hours per Week</span>
                          <span className="text-white font-semibold">{userData.max_hours_per_week}h</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Min Rest Hours</span>
                          <span className="text-white font-semibold">{userData.min_rest_hours}h</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4">Skills</h3>
                      <div className="flex flex-wrap gap-2">
                        {userData.skills && userData.skills.length > 0 ? (
                          userData.skills.map((skill, index) => (
                            <span
                              key={index}
                              className="px-3 py-1 bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30 rounded-full text-white text-sm"
                            >
                              {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-gray-400 italic">No skills listed</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Teams Section */}
              <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl p-8 border border-white/20 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>
                
                <div className="relative z-10">
                  <div className="flex items-center gap-4 mb-8">
                    <div className="p-4 bg-gradient-to-br from-blue-500 to-purple-500 rounded-2xl shadow-lg shadow-blue-500/50">
                      <Users className="w-8 h-8 text-white" />
                    </div>
                    <div>
                      <h3 className="text-3xl font-bold text-white">My Teams</h3>
                      <p className="text-gray-300 mt-1">Teams you are currently assigned to</p>
                    </div>
                  </div>

                  {userData.teams && userData.teams.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {userData.teams.map((team) => (
                        <div
                          key={team.id}
                          className="backdrop-blur-xl bg-white/5 rounded-xl border border-white/10 p-6 hover:bg-white/10 transition-all duration-200"
                        >
                          <div className="flex items-center gap-3 mb-4">
                            <div className={`p-2 rounded-lg ${
                              team.is_active ? 'bg-gradient-to-br from-green-500 to-emerald-500' : 'bg-gradient-to-br from-red-500 to-pink-500'
                            }`}>
                              <Users className="w-5 h-5 text-white" />
                            </div>
                            <div>
                              <h4 className="text-lg font-semibold text-white">{team.name}</h4>
                              <p className="text-sm text-gray-400">{team.member_count} members</p>
                            </div>
                          </div>
                          <div className="flex justify-between items-center text-sm">
                            <span className="text-gray-300">Joined:</span>
                            <span className="text-white">{formatDate(team.created_at)}</span>
                          </div>
                          <div className="flex justify-between items-center text-sm mt-2">
                            <span className="text-gray-300">Status:</span>
                            <span className={`font-semibold ${
                              team.is_active ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {team.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="p-4 bg-white/10 rounded-full w-20 h-20 mx-auto mb-4 flex items-center justify-center">
                        <Users className="w-10 h-10 text-gray-400" />
                      </div>
                      <h4 className="text-xl text-gray-300 mb-2">No Teams Assigned</h4>
                      <p className="text-gray-400">You haven't been assigned to any teams yet.</p>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}