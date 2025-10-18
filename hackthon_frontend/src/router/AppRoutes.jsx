import { Routes, Route } from "react-router-dom";
import React from "react";
import LoginPage from "../pages/public/LoginPage";
import AdminDashboard from "../pages/admin/AdminDashboard";
import AdminAddUser from "../pages/admin/AdminAddUser";
import AdminAddTeam from "../pages/admin/AdminAddTeam";
import AdminAddTeamMember from "../pages/admin/AdminAddTeamMember";
import AdminViewTeam from "../pages/admin/AdminViewTeam";
import AdminManageUser from "../pages/admin/AdminManageUser";
import NotFound from "../components/NotFound";


const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<LoginPage/>} />
      <Route path="/admin_home_page" element={<AdminDashboard/>} />
      <Route path="/add-user" element={<AdminAddUser/>} />
      <Route path="/manage-users" element={<AdminManageUser/>} />
      <Route path="/add-team" element={<AdminAddTeam/>} />
      <Route path="/view-teams" element={<AdminViewTeam/>} />
      <Route path="/add-team-member" element={<AdminAddTeamMember/>} />
      <Route path="/add-team-member/:teamId" element={<AdminAddTeamMember/>} />
      {/* Add UserHomePage route when it's created */}
      <Route path="/user_home_page" element={<div className="min-h-screen flex items-center justify-center bg-gray-900 text-white"><h1 className="text-4xl">User Home Page - Coming Soon</h1></div>} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export default AppRoutes;
