import { Routes, Route } from "react-router-dom";
import React from "react";
import LoginPage from "../pages/public/LoginPage";
import AdminDashboard from "../pages/admin/AdminDashboard";
import AdminAddUser from "../pages/admin/AdminAddUser";
import AdminAddTeam from "../pages/admin/AdminAddTeam";
import AdminAddTeamMember from "../pages/admin/AdminAddTeamMember";


const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<LoginPage/>} />
      <Route path="/admin_home_page" element={<AdminDashboard/>} />
      <Route path="/add-user" element={<AdminAddUser/>} />
      <Route path="/add-team" element={<AdminAddTeam/>} />
      <Route path="/add-team-member" element={<AdminAddTeamMember/>} />
      {/* Add UserHomePage route when it's created */}
      <Route path="/user_home_page" element={<div className="min-h-screen flex items-center justify-center bg-gray-900 text-white"><h1 className="text-4xl">User Home Page - Coming Soon</h1></div>} />
    </Routes>
  );
};

export default AppRoutes;
