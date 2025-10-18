import { Routes, Route } from "react-router-dom";
import React from "react";
import LoginPage from "../pages/public/LoginPage";
import AdminDashboard from "../pages/admin/AdminDashboard";
import AdminAddUser from "../pages/admin/AdminAddUser";
import AdminAddTeam from "../pages/admin/AdminAddTeam";
import AdminAddTeamMember from "../pages/admin/AdminAddTeamMember";
import AdminViewTeam from "../pages/admin/AdminViewTeam";
import AdminViewTeamMembers from "../pages/admin/AdminViewTeamMembers";
import AdminManageUser from "../pages/admin/AdminManageUser";
import AdminNotifications from "../pages/admin/AdminNotifications";
import AdminViewLeave from "../pages/admin/AdminViewLeave";
import UserHomePage from "../pages/user/UserHomePage";
import UserViewSchedule from "../pages/user/UserViewSchedule";
import SwapRequests from "../pages/user/SwapRequests";
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
      <Route path="/view-team-members/:teamId" element={<AdminViewTeamMembers/>} />
      <Route path="/add-team-member" element={<AdminAddTeamMember/>} />
      <Route path="/add-team-member/:teamId" element={<AdminAddTeamMember/>} />
      <Route path="/admin-notifications" element={<AdminNotifications/>} />
      <Route path="/admin/leave-requests" element={<AdminViewLeave/>} />
      <Route path="/user/home" element={<UserHomePage/>} />
      <Route path="/user/schedule" element={<UserViewSchedule/>} />
      <Route path="/user/swap-requests" element={<SwapRequests/>} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export default AppRoutes;
