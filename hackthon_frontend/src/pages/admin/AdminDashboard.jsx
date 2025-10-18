import React, { useState } from "react";
import { Users, UserPlus, Calendar, Clock, BarChart3, Settings, LogOut, Menu, X, Zap, TrendingUp, Shield, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../../components/Sidebar";

export default function AdminDashboard() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const navigate = useNavigate();

  const stats = [
    {
      title: "Total Users",
      value: "248",
      change: "+12.5%",
      trend: "up",
      icon: Users,
      gradient: "from-purple-500 to-blue-500",
    },
    {
      title: "Active Teams",
      value: "32",
      change: "+8.2%",
      trend: "up",
      icon: Calendar,
      gradient: "from-emerald-500 to-teal-500",
    },
    {
      title: "Total Managers",
      value: "45",
      change: "+5.1%",
      trend: "up",
      icon: Shield,
      gradient: "from-pink-500 to-rose-500",
    },
    {
      title: "Avg Hours/Week",
      value: "38.5",
      change: "-2.3%",
      trend: "down",
      icon: Clock,
      gradient: "from-blue-500 to-indigo-500",
    },
  ];

  const quickActions = [
    {
      title: "Add New User",
      description: "Create a new team member account",
      icon: UserPlus,
      gradient: "from-purple-500 to-blue-500",
      action: () => navigate("/add-user"),
      color: "purple",
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

  const recentActivities = [
    {
      user: "John Doe",
      action: "created a new team",
      team: "Engineering Alpha",
      time: "2 hours ago",
      type: "team",
    },
    {
      user: "Sarah Smith",
      action: "added a new user",
      team: "Jane Wilson",
      time: "4 hours ago",
      type: "user",
    },
    {
      user: "Mike Johnson",
      action: "updated team settings",
      team: "Design Team",
      time: "6 hours ago",
      type: "settings",
    },
    {
      user: "Emily Davis",
      action: "created a new team",
      team: "Marketing Pro",
      time: "1 day ago",
      type: "team",
    },
  ];

  return (
    <div className="min-h-screen h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex overflow-hidden">
      <div className="absolute top-0 left-0 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
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
                  className="pl-10 pr-4 py-2 bg-white/10 backdrop-blur-sm border border-white/30 rounded-xl text-white placeholder-gray-400 focus:bg-white/20 focus:ring-2 focus:ring-purple-500 focus:outline-none transition-all"
                />
              </div>

              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center shadow-lg cursor-pointer">
                <span className="text-white font-semibold">AD</span>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {stats.map((stat, index) => (
              <div
                key={index}
                className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 bg-gradient-to-br ${stat.gradient} rounded-xl shadow-lg`}>
                    <stat.icon className="w-6 h-6 text-white" />
                  </div>
                  <span className={`text-sm font-semibold ${stat.trend === 'up' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {stat.change}
                  </span>
                </div>
                <h3 className="text-gray-300 text-sm mb-1">{stat.title}</h3>
                <p className="text-white text-3xl font-bold">{stat.value}</p>
              </div>
            ))}
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
              <button className="text-purple-300 hover:text-purple-200 text-sm font-medium transition-colors">
                View All
              </button>
            </div>

            <div className="space-y-4">
              {recentActivities.map((activity, index) => (
                <div
                  key={index}
                  className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10 hover:bg-white/10 transition-all"
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${
                      activity.type === 'team' ? 'bg-gradient-to-br from-blue-500 to-indigo-500' :
                      activity.type === 'user' ? 'bg-gradient-to-br from-purple-500 to-pink-500' :
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
                        <span className="font-semibold">{activity.team}</span>
                      </p>
                      <p className="text-gray-400 text-sm">{activity.time}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}