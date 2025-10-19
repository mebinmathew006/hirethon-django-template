import React from "react";
import { Users, UserPlus, Calendar, Settings, LogOut, Menu, X, BarChart3, UserCheck, UserCog, Bell, CalendarDays, RotateCcw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { destroyDetails } from "../store/UserDetailsSlice";
import { logoutRoute } from "../services/userService";
import { toast } from "react-toastify";

export default function Sidebar({ isSidebarOpen, setIsSidebarOpen }) {
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
      // Even if the logout request fails, we should clear local state
      dispatch(destroyDetails());
      toast.error("Error during logout, but you have been logged out locally", {
        position: "bottom-center",
      });
      navigate("/");
    }
  };

  return (
    <div className={`relative z-20 ${isSidebarOpen ? 'w-72' : 'w-20'} transition-all duration-300 backdrop-blur-xl bg-white/5 border-r border-white/10`}>
      <div className="flex flex-col h-full p-4">
        <div className="flex items-center justify-between mb-8">
          {isSidebarOpen && (
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-grey-500 to-blue-500 rounded-xl shadow-lg">
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

        <nav className="flex-1 space-y-2">
          <button 
            onClick={() => navigate("/admin_home_page")} 
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-gradient-to-r from-grey-600 to-blue-500 text-white shadow-lg shadow-grey-500/50 transition-all"
          >
            <BarChart3 className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Dashboard</span>}
          </button>

          <button 
            onClick={() => navigate("/add-user")}  
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 transition-all"
          >
            <UserPlus className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Add User</span>}
          </button>

          <button 
            onClick={() => navigate("/manage-users")}  
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 transition-all"
          >
            <UserCog className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Manage Users</span>}
          </button>

          <button 
            onClick={() => navigate("/add-team")}  
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 transition-all"
          >
            <Users className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Add Team</span>}
          </button>

          <button 
            onClick={() => navigate("/view-teams")}  
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 transition-all"
          >
            <UserCheck className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Manage Teams</span>}
          </button>

          <button 
            onClick={() => navigate("/admin-notifications")}  
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 transition-all"
          >
            <Bell className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Notifications</span>}
          </button>

          <button 
            onClick={() => navigate("/admin/leave-requests")}  
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 transition-all"
          >
            <CalendarDays className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Leave Requests</span>}
          </button>

          <button 
            onClick={() => navigate("/admin/swap-requests")}  
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 transition-all"
          >
            <RotateCcw className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Swap Requests</span>}
          </button>

          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 transition-all">
            <Calendar className="w-5 h-5" />
            {isSidebarOpen && <span className="font-medium">Schedules</span>}
          </button>

          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 transition-all">
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