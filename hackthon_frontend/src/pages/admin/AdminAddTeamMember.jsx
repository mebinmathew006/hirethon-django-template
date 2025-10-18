import React, { useState, useEffect } from "react";
import { Users, Calendar, ArrowLeft, Clock, Zap, Shield, UserPlus } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { createTeamMemberRoute, createTeamMemberForTeamRoute, getTeamsListRoute, getUsersListRoute, getTeamsManagementRoute } from "../../services/userService";
import { toast } from "react-toastify";
import Sidebar from "../../components/Sidebar";

export default function AdminAddTeamMember() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { teamId } = useParams();

  const [formData, setFormData] = useState({
    user: "",
    is_manager: false,
  });

  const [team, setTeam] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch team and users data on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        if (teamId) {
          // If teamId is provided, fetch specific team data and users
          const [teamsResponse, usersResponse] = await Promise.all([
            getTeamsManagementRoute(),
            getUsersListRoute()
          ]);

          if (teamsResponse.status === 200) {
            const selectedTeam = teamsResponse.data.teams.find(t => t.id.toString() === teamId);
            if (selectedTeam) {
              setTeam(selectedTeam);
            } else {
              toast.error("Team not found", { position: "bottom-center" });
              navigate("/view-teams");
            }
          }

          if (usersResponse.status === 200) {
            setUsers(usersResponse.data.users || []);
          }
        } else {
          // If no teamId, fetch all teams and users (legacy support)
          const [teamsResponse, usersResponse] = await Promise.all([
            getTeamsListRoute(),
            getUsersListRoute()
          ]);

          if (teamsResponse.status === 200) {
            setTeam({ id: "", name: "Select Team" });
          }

          if (usersResponse.status === 200) {
            setUsers(usersResponse.data.users || []);
          }
        }
      } catch (error) {
        console.error("Error fetching data:", error);
        toast.error("Failed to load data", {
          position: "bottom-center",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [teamId, navigate]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });

    if (touched[name]) {
      validateField(name, type === 'checkbox' ? checked : value);
    }
  };

  const handleBlur = (e) => {
    const { name, value, type } = e.target;
    setTouched({
      ...touched,
      [name]: true,
    });
    validateField(name, type === 'checkbox' ? e.target.checked : value);
  };

  const validateField = (name, value) => {
    let newErrors = { ...errors };

    switch (name) {
      case "user":
        if (!value) {
          newErrors.user = "Please select a user";
        } else {
          delete newErrors.user;
        }
        break;

      default:
        break;
    }
    setErrors(newErrors);
  };

  const validateForm = () => {
    const newErrors = {};

    if (teamId && !team) {
      newErrors.team = "Team not found";
    }

    if (!formData.user) {
      newErrors.user = "Please select a user";
    }

    setErrors(newErrors);

    const touchedFields = {};
    Object.keys(formData).forEach((key) => {
      touchedFields[key] = true;
    });
    setTouched(touchedFields);

    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    if (validateForm()) {
      try {
        const teamMemberData = {
          user: parseInt(formData.user),
          is_manager: formData.is_manager,
        };

        let response;
        if (teamId) {
          // Use the team-specific endpoint
          response = await createTeamMemberForTeamRoute(teamId, teamMemberData);
        } else {
          // Use the general endpoint (legacy support)
          teamMemberData.team = parseInt(formData.team);
          response = await createTeamMemberRoute(teamMemberData);
        }
        
        if (response.status === 201) {
          toast.success("User added to team successfully!", {
            position: "bottom-center",
          });
          
          // Reset form
          setFormData({
            user: "",
            is_manager: false,
          });
          setErrors({});
          setTouched({});
          
          // Navigate back to appropriate page
          setTimeout(() => {
            if (teamId) {
              navigate("/view-teams");
            } else {
              navigate("/admin_home_page");
            }
          }, 1500);
        }
      } catch (error) {
        console.error("Error adding team member:", error);
        
        if (error.response && error.response.data && error.response.data.error) {
          const backendErrors = {};
          
          if (error.response.data.error.team) {
            backendErrors.team = Array.isArray(error.response.data.error.team) 
              ? error.response.data.error.team[0] 
              : error.response.data.error.team;
          }
          if (error.response.data.error.user) {
            backendErrors.user = Array.isArray(error.response.data.error.user)
              ? error.response.data.error.user[0]
              : error.response.data.error.user;
          }
          if (error.response.data.error.commonError) {
            toast.error(error.response.data.error.commonError, {
              position: "bottom-center",
            });
          }
          
          setErrors({ ...errors, ...backendErrors });
        } else {
          toast.error("Failed to add team member. Please try again.", {
            position: "bottom-center",
          });
        }
      }
    }
    
    setIsSubmitting(false);
  };

  const getSelectedTeam = () => {
    return team;
  };

  const getSelectedUser = () => {
    return users.find(user => user.id.toString() === formData.user);
  };

  if (loading) {
    return (
      <div className="min-h-screen h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span className="text-white text-lg">Loading...</span>
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
        <div className="max-w-4xl mx-auto p-8">
          <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-purple-300 hover:text-purple-200 transition-colors mb-8 group">
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back to Dashboard</span>
          </button>

          <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl p-8 lg:p-12 border border-white/20 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>

            <div className="relative z-10">
              <div className="flex items-center gap-4 mb-8">
                <div className="p-4 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl shadow-lg shadow-emerald-500/50">
                  <UserPlus className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold text-white">
                    {teamId && team ? `Add Member to ${team.name}` : 'Add Team Member'}
                  </h1>
                  <p className="text-gray-300 mt-1">
                    {teamId && team ? 'Add a user to this team and configure their role' : 'Assign users to teams and configure their roles'}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-lg">
                      <Users className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Smart</p>
                      <p className="text-white font-semibold">Assignment</p>
                    </div>
                  </div>
                </div>

                <div className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-lg">
                      <Clock className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Role</p>
                      <p className="text-white font-semibold">Management</p>
                    </div>
                  </div>
                </div>

                <div className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-br from-pink-500 to-rose-500 rounded-lg">
                      <Zap className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Instant</p>
                      <p className="text-white font-semibold">Assignment</p>
                    </div>
                  </div>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                {teamId && team ? (
                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">
                      Team
                    </label>
                    <div className="w-full px-4 py-4 bg-white/10 backdrop-blur-sm border border-white/30 rounded-xl text-white shadow-lg text-lg">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg">
                          <Users className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <p className="font-semibold">{team.name}</p>
                          <p className="text-sm text-gray-300">{team.member_count} members</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : !teamId ? (
                  <div>
                    <label htmlFor="team" className="block text-sm font-semibold text-white mb-2">
                      Select Team *
                    </label>
                    <select
                      id="team"
                      name="team"
                      value={formData.team || ""}
                      onChange={handleChange}
                      onBlur={handleBlur}
                      className="w-full px-4 py-4 bg-white/10 backdrop-blur-sm border border-white/30 rounded-xl text-white focus:bg-white/20 focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:outline-none transition-all duration-300 shadow-lg text-lg"
                    >
                      <option value="" className="bg-gray-800">Choose a team...</option>
                      {/* This will be handled by legacy support */}
                    </select>
                    {errors.team && touched.team && (
                      <p className="mt-2 text-sm text-red-300">{errors.team}</p>
                    )}
                  </div>
                ) : null}

                <div>
                  <label htmlFor="user" className="block text-sm font-semibold text-white mb-2">
                    Select User *
                  </label>
                  <select
                    id="user"
                    name="user"
                    value={formData.user}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    className="w-full px-4 py-4 bg-white/10 backdrop-blur-sm border border-white/30 rounded-xl text-white focus:bg-white/20 focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:outline-none transition-all duration-300 shadow-lg text-lg"
                  >
                    <option value="" className="bg-gray-800">Choose a user...</option>
                    {users.map((user) => (
                      <option key={user.id} value={user.id} className="bg-gray-800">
                        {user.name} ({user.email})
                      </option>
                    ))}
                  </select>
                  {errors.user && touched.user && (
                    <p className="mt-2 text-sm text-red-300">{errors.user}</p>
                  )}
                </div>

                <div className="backdrop-blur-xl bg-white/5 rounded-xl p-6 border border-white/10">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg">
                        <Shield className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="text-white font-semibold">Team Manager</h3>
                        <p className="text-sm text-gray-300">Grant manager privileges for this member</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        name="is_manager"
                        checked={formData.is_manager}
                        onChange={handleChange}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>
                </div>

                {/* Selected Information Display */}
                {(formData.team || formData.user) && (
                  <div className="backdrop-blur-xl bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-xl p-6 border border-purple-500/30">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg mt-1">
                        <Calendar className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="text-white font-semibold mb-2">Assignment Summary</h3>
                        <div className="space-y-2 text-sm text-gray-300">
                          {getSelectedUser() && (
                            <p><span className="font-medium text-white">User:</span> {getSelectedUser().name} ({getSelectedUser().email})</p>
                          )}
                          {getSelectedTeam() && (
                            <p><span className="font-medium text-white">Team:</span> {getSelectedTeam().name}</p>
                          )}
                          <p><span className="font-medium text-white">Role:</span> {formData.is_manager ? 'Team Manager' : 'Team Member'}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-4 pt-6">
                  <button
                    type="submit"
                    disabled={isSubmitting || (!teamId && !team) || users.length === 0}
                    className="flex-1 bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-500 hover:from-emerald-500 hover:via-emerald-400 hover:to-teal-400 text-white py-4 px-6 rounded-2xl font-bold text-lg shadow-2xl shadow-emerald-500/50 hover:shadow-emerald-400/60 focus:outline-none focus:ring-4 focus:ring-emerald-500/50 transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 relative overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="relative z-10">
                      {isSubmitting ? (
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Adding Member...
                        </div>
                      ) : (
                        "Add Team Member"
                      )}
                    </span>
                    <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-700"></div>
                  </button>

                  <button
                    type="button"
                    onClick={() => navigate("/admin_home_page")}
                    className="px-8 py-4 bg-white/10 backdrop-blur-sm hover:bg-white/20 border border-white/30 text-white rounded-2xl font-semibold shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-white/50 transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
