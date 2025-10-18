import React, { useState, useEffect } from "react";
import { Users, UserPlus, Calendar, Clock, BarChart3, Settings, LogOut, Menu, X, Zap, TrendingUp, Shield, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getDashboardStatsRoute } from "../../services/userService";
import { toast } from "react-toastify";
import Sidebar from "../../components/Sidebar";

export default function AdminDashboard() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    stats: {
      total_users: 0,
      active_users: 0,
      total_teams: 0,
      active_teams: 0,
      total_managers: 0,
      active_managers: 0,
      avg_hours_per_week: 0
    },
    recent_activities: []
  });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await getDashboardStatsRoute();
      
      if (response.status === 200) {
        setDashboardData(response.data);
      }
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      toast.error("Failed to load dashboard data", {
        position: "bottom-center",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Dynamic stats based on fetched data
  const stats = [
    {
      title: "Total Users",
      value: dashboardData.stats.total_users?.toString() || "0",
      change: "+0%", // Could calculate trends from historical data
      trend: "up",
      icon: Users,
      gradient: "from-grey-500 to-blue-500",
    },
    {
      title: "Active Teams",
      value: dashboardData.stats.active_teams?.toString() || "0",
      change: "+0%",
      trend: "up",
      icon: Calendar,
      gradient: "from-emerald-500 to-teal-500",
    },
    {
      title: "Total Managers",
      value: dashboardData.stats.total_managers?.toString() || "0",
      change: "+0%",
      trend: "up",
      icon: Shield,
      gradient: "from-pink-500 to-rose-500",
    },
    {
      title: "Avg Hours/Week",
      value: dashboardData.stats.avg_hours_per_week?.toString() || "0",
      change: "0%",
      trend: "neutral",
      icon: Clock,
      gradient: "from-blue-500 to-indigo-500",
    },
  ];

  const quickActions = [
    {
      title: "Add New User",
      description: "Create a new team member account",
      icon: UserPlus,
      gradient: "from-grey-500 to-blue-500",
      action: () => navigate("/add-user"),
      color: "grey",
    },
    {
      title: "Create Team",
      description: "Set up a new team with scheduling",
      icon: Users,
      gradient: "from-blue-500 to-indigo-500",
      action: () => navigate("/add-team"),
      color: "blue",
    },
    {
      title: "View Reports",
      description: "Analytics and performance metrics",
      icon: BarChart3,
      gradient: "from-emerald-500 to-teal-500",
      action: () => console.log("Navigate to Reports"),
      color: "emerald",
    },
    {
      title: "System Settings",
      description: "Configure application preferences",
      icon: Settings,
      gradient: "from-pink-500 to-rose-500",
      action: () => console.log("Navigate to Settings"),
      color: "pink",
    },
  ];

  // Helper function to format activity display
  const formatActivity = (activity) => {
    switch (activity.type) {
      case 'team_created':
        return {
          user: activity.created_by || 'System',
          action: 'created a new team',
          team: activity.team_name,
          time: activity.time_ago,
          type: 'team'
        };
      case 'user_created':
        return {
          user: activity.created_by || 'System',
          action: 'added a new user',
          team: activity.user_name,
          time: activity.time_ago,
          type: 'user'
        };
      case 'leave_requested':
        return {
          user: activity.user_name,
          action: 'requested leave',
          team: activity.team_name,
          time: activity.time_ago,
          type: 'settings',
          status: activity.status,
          date: activity.date
        };
      default:
        return {
          user: 'System',
          action: activity.type,
          team: '',
          time: activity.time_ago || 'Unknown',
          type: 'settings'
        };
    }
  };

  const recentActivities = dashboardData.recent_activities.map(formatActivity);

  return (
    <div className="min-h-screen h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex overflow-hidden">
      <div className="absolute top-0 left-0 w-96 h-96 bg-grey-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '700ms'}}></div>
      <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '1000ms'}}></div>

      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:100px_100px]"></div>

      {/* Sidebar Component */}
      <Sidebar isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />

      {/* Main Content */}
      <div className="flex-1 relative z-10 overflow-y-auto">
        <div className="p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-4xl font-bold text-white mb-2">Admin Dashboard</h2>
              <p className="text-gray-300">Welcome back! Here's what's happening today.</p>
            </div>

            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search..."
                  className="pl-10 pr-4 py-2 bg-white/10 backdrop-blur-sm border border-white/30 rounded-xl text-white placeholder-gray-400 focus:bg-white/20 focus:ring-2 focus:ring-grey-500 focus:outline-none transition-all"
                />
              </div>

              <div className="w-10 h-10 bg-gradient-to-br from-grey-500 to-blue-500 rounded-full flex items-center justify-center shadow-lg cursor-pointer">
                <span className="text-white font-semibold">AD</span>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {loading ? (
              // Loading skeleton for stats
              [...Array(4)].map((_, index) => (
                <div
                  key={index}
                  className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl animate-pulse"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 bg-gray-600 rounded-xl">
                      <div className="w-6 h-6 bg-gray-400 rounded"></div>
                    </div>
                    <div className="w-12 h-4 bg-gray-600 rounded"></div>
                  </div>
                  <div className="w-20 h-4 bg-gray-600 rounded mb-2"></div>
                  <div className="w-16 h-8 bg-gray-600 rounded"></div>
                </div>
              ))
            ) : (
              stats.map((stat, index) => (
                <div
                  key={index}
                  className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className={`p-3 bg-gradient-to-br ${stat.gradient} rounded-xl shadow-lg`}>
                      <stat.icon className="w-6 h-6 text-white" />
                    </div>
                    <span className={`text-sm font-semibold ${stat.trend === 'up' ? 'text-emerald-400' : stat.trend === 'down' ? 'text-red-400' : 'text-gray-400'}`}>
                      {stat.change}
                    </span>
                  </div>
                  <h3 className="text-gray-300 text-sm mb-1">{stat.title}</h3>
                  <p className="text-white text-3xl font-bold">{stat.value}</p>
                </div>
              ))
            )}
          </div>

          {/* Quick Actions */}
          <div className="mb-8">
            <h3 className="text-2xl font-bold text-white mb-6">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.action}
                  className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 text-left group"
                >
                  <div className={`p-4 bg-gradient-to-br ${action.gradient} rounded-xl shadow-lg mb-4 inline-block group-hover:scale-110 transition-transform`}>
                    <action.icon className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="text-white font-semibold text-lg mb-2">{action.title}</h4>
                  <p className="text-gray-300 text-sm">{action.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-white">Recent Activity</h3>
              <button className="text-grey-300 hover:text-grey-200 text-sm font-medium transition-colors">
                View All
              </button>
            </div>

            <div className="space-y-4">
              {loading ? (
                // Loading skeleton for recent activities
                [...Array(4)].map((_, index) => (
                  <div
                    key={index}
                    className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10 animate-pulse"
                  >
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-gray-600 rounded-lg">
                        <div className="w-5 h-5 bg-gray-400 rounded"></div>
                      </div>
                      <div className="flex-1">
                        <div className="w-48 h-4 bg-gray-600 rounded mb-2"></div>
                        <div className="w-20 h-3 bg-gray-600 rounded"></div>
                      </div>
                    </div>
                  </div>
                ))
              ) : recentActivities.length > 0 ? (
                recentActivities.map((activity, index) => (
                  <div
                    key={index}
                    className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10 hover:bg-white/10 transition-all"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`p-2 rounded-lg ${
                        activity.type === 'team' ? 'bg-gradient-to-br from-blue-500 to-indigo-500' :
                        activity.type === 'user' ? 'bg-gradient-to-br from-grey-500 to-pink-500' :
                        'bg-gradient-to-br from-emerald-500 to-teal-500'
                      }`}>
                        {activity.type === 'team' ? <Users className="w-5 h-5 text-white" /> :
                         activity.type === 'user' ? <UserPlus className="w-5 h-5 text-white" /> :
                         <Settings className="w-5 h-5 text-white" />}
                      </div>
                      <div className="flex-1">
                        <p className="text-white">
                          <span className="font-semibold">{activity.user}</span>
                          <span className="text-gray-300"> {activity.action} </span>
                          {activity.team && <span className="font-semibold">{activity.team}</span>}
                        </p>
                        <p className="text-gray-400 text-sm">{activity.time}</p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <div className="p-4 bg-white/10 rounded-full w-20 h-20 mx-auto mb-4 flex items-center justify-center">
                    <Users className="w-10 h-10 text-gray-400" />
                  </div>
                  <h3 className="text-xl text-gray-300 mb-2">No Recent Activity</h3>
                  <p className="text-gray-400">Recent team and user activities will appear here.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}