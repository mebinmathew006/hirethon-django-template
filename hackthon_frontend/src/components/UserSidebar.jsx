import React from "react";
import { Users, Calendar, Clock4, User, Shield, Settings, LogOut, Menu, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { destroyDetails } from "../store/UserDetailsSlice";
import { logoutRoute } from "../services/userService";
import { toast } from "react-toastify";

export default function UserSidebar({ 
  isSidebarOpen, 
  setIsSidebarOpen, 
  userData, 
  activeTab = "dashboard" 
}) {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const handleLogout = async () => {
    try {
      await logoutRoute();
      dispatch(destroyDetails());
      toast.success("Logged out successfully", {
        position: "bottom-center",
      });
      navigate("/");
    } catch (error) {
      console.error("Logout error:", error);
      dispatch(destroyDetails());
      toast.error("Error during logout, but you have been logged out locally", {
        position: "bottom-center",
      });
      navigate("/");
    }
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
        return <Shield className="w-5 h-5" />;
      case 'manager':
        return <User className="w-5 h-5" />;
      case 'doctor':
        return <Users className="w-5 h-5" />;
      default:
        return <User className="w-5 h-5" />;
    }
  };

  return (
    <div className={`relative z-20 ${isSidebarOpen ? 'w-72' : 'w-20'} transition-all duration-300 backdrop-blur-xl bg-white/5 border-r border-white/10`}>
      <div className="flex flex-col h-full p-4">
        <div className="flex items-center justify-between mb-8">
          {isSidebarOpen && (
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl shadow-lg">
                <Calendar className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-white">TimeSync</h1>
            </div>
          )}
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            {isSidebarOpen ? (
              <X className="w-6 h-6 text-white" />
            ) : (
              <Menu className="w-6 h-6 text-white" />
            )}
          </button>
        </div>

        {/* User Profile Section */}
        {userData && (
          <div className="mb-8 p-4 bg-white/5 rounded-xl border border-white/10">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-gradient-to-br ${getRoleColor(userData.role)}`}>
                {getRoleIcon(userData.role)}
              </div>
              {isSidebarOpen && (
                <div>
                  <h3 className="text-white font-semibold">{userData.name}</h3>
                  <p className="text-xs text-gray-400 capitalize">{userData.role}</p>
                </div>
              )}
            </div>
          </div>
        )}

        <nav className="flex-1 space-y-2">
          <button 
            onClick={() => navigate("/user/home")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === "dashboard" 
                ? "bg-gradient-to-r from-purple-600 to-blue-500 text-white shadow-lg shadow-purple-500/50" 
                : "text-gray-300 hover:bg-white/10"
            }`}
          >
            <Clock4 className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Dashboard</span>}
          </button>

          <button 
            onClick={() => navigate("/user/schedule")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === "schedule" 
                ? "bg-gradient-to-r from-purple-600 to-blue-500 text-white shadow-lg shadow-purple-500/50" 
                : "text-gray-300 hover:bg-white/10"
            }`}
          >
            <Calendar className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">My Schedule</span>}
          </button>

          <button 
            onClick={() => navigate("/user/teams")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === "teams" 
                ? "bg-gradient-to-r from-purple-600 to-blue-500 text-white shadow-lg shadow-purple-500/50" 
                : "text-gray-300 hover:bg-white/10"
            }`}
          >
            <Users className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">My Teams</span>}
          </button>

          <button 
            onClick={() => navigate("/user/settings")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === "settings" 
                ? "bg-gradient-to-r from-purple-600 to-blue-500 text-white shadow-lg shadow-purple-500/50" 
                : "text-gray-300 hover:bg-white/10"
            }`}
          >
            <Settings className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Settings</span>}
          </button>
        </nav>

        <button 
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-300 hover:bg-red-500/10 transition-all mt-4"
        >
          <LogOut className="w-5 h-5" />
          {isSidebarOpen && <span className="font-medium">Logout</span>}
        </button>
      </div>
    </div>
  );
}