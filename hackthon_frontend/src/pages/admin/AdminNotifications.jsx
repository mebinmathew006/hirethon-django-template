import React, { useState, useEffect } from "react";
import { ArrowLeft, Bell, Clock, AlertTriangle, Users, Calendar, X, Check, UserPlus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import Sidebar from "../../components/Sidebar";
import { toast } from "react-toastify";
import axiosInstance from "../../api/axiosconfig";
import { getAvailableUsersForSlotRoute, assignUserToSlotRoute } from "../../services/userService";

export default function AdminNotifications() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [assignSlotModalOpen, setAssignSlotModalOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [assigningUser, setAssigningUser] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const navigate = useNavigate();
  
  // Get access token from Redux state
  const accessToken = useSelector(state => state.userDetails.access_token);

  // Fetch notifications on component mount and set up WebSocket
  useEffect(() => {
    fetchNotifications();
    
    // Set up WebSocket connection for real-time notifications
    let ws = null;
    
    const connectWebSocket = () => {
      try {
        // Close existing connection if any
        if (ws) {
          ws.close(1000, 'Reconnecting with new token');
        }
        
        // Get access token from Redux state first, fallback to localStorage
        const token = accessToken || localStorage.getItem('access_token');
        const tokenSource = accessToken ? 'Redux' : 'localStorage';
        
        // Don't try to connect if we don't have a token yet
        if (!token) {
          console.log('No access token available in Redux or localStorage, skipping WebSocket connection');
          console.log('Redux accessToken:', accessToken ? 'present' : 'missing');
          console.log('localStorage token:', localStorage.getItem('access_token') ? 'present' : 'missing');
          return;
        }
        
        // Use WebSocket for real-time notifications
        // Get the backend URL from the same environment variable used by axios
        const baseurl = import.meta.env.VITE_BASE_URL;
        
        if (!baseurl) {
          console.error('VITE_BASE_URL is not defined');
          return;
        }
        
        let wsUrl;
        try {
          const backendUrl = new URL(baseurl);
          const wsProtocol = backendUrl.protocol === 'https:' ? 'wss:' : 'ws:';
          wsUrl = `${wsProtocol}//${backendUrl.host}/ws/notifications/?token=${token}`;
        } catch (error) {
          console.error('Error parsing backend URL:', error, 'baseurl:', baseurl);
          return;
        }
        
        console.log(`Connecting to WebSocket with token from ${tokenSource}:`, token.substring(0, 20) + '...');
        console.log('Backend base URL:', baseurl);
        console.log('WebSocket URL:', wsUrl);
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log('WebSocket connected for notifications');
          // Send a ping to test connection
          ws.send(JSON.stringify({ type: 'ping' }));
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'empty_slot_alert') {
              // Add new notification to the state
              setNotifications(prev => {
                // Avoid duplicates
                const exists = prev.some(notif => notif.slot_id === data.data.slot_id);
                if (!exists) {
                  return [data.data, ...prev];
                }
                return prev;
              });
              
              // Show toast notification
              toast.warning(`New empty slot detected: ${data.data.team_name}`, {
                position: "bottom-center",
                autoClose: 5000,
              });
            } else if (data.type === 'pong') {
              console.log('WebSocket pong received');
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
        
        ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          
          // Attempt to reconnect after 5 seconds if not a normal closure
          if (event.code !== 1000) {
            setTimeout(connectWebSocket, 5000);
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
        
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        // Fallback to polling if WebSocket fails
        ws = null;
      }
    };
    
    // Only connect if we have an access token (from Redux or localStorage)
    if (accessToken || localStorage.getItem('access_token')) {
      connectWebSocket();
    }
    
    // Fallback polling in case WebSocket fails (every 60 seconds as backup)
    const fallbackInterval = setInterval(fetchNotifications, 60000);
    
    return () => {
      if (ws) {
        ws.close(1000, 'Component unmounting');
      }
      clearInterval(fallbackInterval);
    };
  }, [accessToken]); // Re-run when accessToken changes

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axiosInstance.get('/api/managers/notifications/');
      
      if (response.status === 200) {
        setNotifications(response.data.notifications || []);
      }
    } catch (error) {
      console.error("Error fetching notifications:", error);
      setError("Failed to load notifications");
      toast.error("Failed to load notifications", {
        position: "bottom-center",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId) => {
    try {
      const response = await axiosInstance.post('/api/managers/mark-notification-read/', {
        notification_id: notificationId
      });
      
      if (response.status === 200) {
        // Remove the notification from the local state
        setNotifications(prev => prev.filter(notif => notif.slot_id !== notificationId));
        
        toast.success("Notification marked as read", {
          position: "bottom-center",
        });
      }
    } catch (error) {
      console.error("Error marking notification as read:", error);
      toast.error("Failed to mark notification as read", {
        position: "bottom-center",
      });
    }
  };

  const formatDateTime = (dateTimeString) => {
    try {
      const date = new Date(dateTimeString);
      return {
        date: date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        }),
        time: date.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        })
      };
    } catch (error) {
      return { date: 'Invalid Date', time: '' };
    }
  };

  const getUrgencyColor = (hoursFromNow) => {
    if (hoursFromNow <= 24) return "text-red-500 bg-red-50 border-red-200";
    if (hoursFromNow <= 48) return "text-orange-500 bg-orange-50 border-orange-200";
    return "text-yellow-500 bg-yellow-50 border-yellow-200";
  };

  const getUrgencyText = (hoursFromNow) => {
    if (hoursFromNow <= 24) return "Critical";
    if (hoursFromNow <= 48) return "High Priority";
    return "Medium Priority";
  };

  const handleManageSlot = async (notification) => {
    try {
      setLoadingUsers(true);
      setSelectedSlot({
        id: notification.slot_id,
        team_name: notification.team_name,
        start_time: notification.start_time,
        end_time: notification.end_time
      });
      
      const response = await getAvailableUsersForSlotRoute(notification.slot_id);
      
      if (response.status === 200) {
        setAvailableUsers(response.data.available_users || []);
        setAssignSlotModalOpen(true);
      }
    } catch (error) {
      console.error("Error fetching available users:", error);
      toast.error("Failed to load available users for this slot", {
        position: "bottom-center",
      });
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleAssignUser = async (userId) => {
    if (!selectedSlot) return;

    try {
      setAssigningUser(true);
      const response = await assignUserToSlotRoute(selectedSlot.id, userId);
      
      if (response.status === 200) {
        toast.success("User assigned to slot successfully", {
          position: "bottom-center",
        });
        
        // Refresh notifications to ensure backend state is synchronized
        await fetchNotifications();
        
        // Close the modal
        setAssignSlotModalOpen(false);
        setSelectedSlot(null);
        setAvailableUsers([]);
      }
    } catch (error) {
      console.error("Error assigning user to slot:", error);
      const errorMessage = error.response?.data?.error?.commonError || "Failed to assign user to slot";
      toast.error(errorMessage, {
        position: "bottom-center",
      });
    } finally {
      setAssigningUser(false);
    }
  };

  const closeAssignModal = () => {
    setAssignSlotModalOpen(false);
    setSelectedSlot(null);
    setAvailableUsers([]);
  };

  if (loading && notifications.length === 0) {
    return (
      <div className="min-h-screen h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span className="text-white text-lg">Loading notifications...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen h-screen bg-gradient-to-br from-black via-gray-800 to-gray-900 flex overflow-hidden">
      {/* Background Effects */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-gray-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '700ms'}}></div>
      <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '1000ms'}}></div>
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:100px_100px]"></div>
      
      <Sidebar isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />
      
      <div className="flex-1 relative z-10 overflow-y-auto">
        <div className="max-w-6xl mx-auto p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <button 
              onClick={() => navigate("/admin_home_page")} 
              className="flex items-center gap-2 text-gray-300 hover:text-gray-200 transition-colors group"
            >
              <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
              <span className="font-medium">Back to Dashboard</span>
            </button>
            
            <div className="flex items-center gap-4">
              <button
                onClick={fetchNotifications}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-all disabled:opacity-50"
              >
                <div className={`w-4 h-4 border border-white border-t-transparent rounded-full ${loading ? 'animate-spin' : ''}`}></div>
                Refresh
              </button>
            </div>
          </div>

          {/* Page Title */}
          <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl p-8 border border-white/20 relative overflow-hidden mb-8">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-gray-500 to-blue-500 rounded-xl">
                <Bell className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">Empty Slots Notifications</h1>
                <p className="text-gray-300">
                  Real-time alerts for unassigned slots in the next 72 hours
                </p>
              </div>
            </div>
          </div>

          {/* Error State */}
          {error && (
            <div className="backdrop-blur-xl bg-red-500/10 rounded-2xl border border-red-500/20 p-6 mb-8">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-6 h-6 text-red-400" />
                <div>
                  <h3 className="text-red-300 font-semibold">Error Loading Notifications</h3>
                  <p className="text-red-200">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Notifications List */}
          <div className="backdrop-blur-xl bg-white/10 rounded-2xl shadow-2xl border border-white/20 overflow-hidden">
            {notifications.length === 0 ? (
              <div className="p-16 text-center">
                <div className="p-4 bg-green-500/20 rounded-full w-20 h-20 mx-auto mb-4 flex items-center justify-center">
                  <Check className="w-10 h-10 text-green-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">All Clear!</h3>
                <p className="text-gray-300">
                  No empty slots found in the next 72 hours. All shifts are properly covered.
                </p>
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="bg-white/5 px-6 py-4 border-b border-white/10">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-white">
                      {notifications.length} Notification{notifications.length !== 1 ? 's' : ''}
                    </h2>
                    <div className="flex items-center gap-2 text-sm text-gray-300">
                      <Clock className="w-4 h-4" />
                      Updates every 30 seconds
                    </div>
                  </div>
                </div>

                {/* Notifications */}
                <div className="divide-y divide-white/10">
                  {notifications.map((notification) => {
                    const startTime = formatDateTime(notification.start_time);
                    const endTime = formatDateTime(notification.end_time);
                    const urgencyColor = getUrgencyColor(notification.hours_from_now);
                    const urgencyText = getUrgencyText(notification.hours_from_now);

                    return (
                      <div key={notification.slot_id} className="p-6 hover:bg-white/5 transition-all">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-start gap-4 flex-1">
                            {/* Urgency Indicator */}
                            <div className={`px-3 py-1 rounded-full text-xs font-semibold border ${urgencyColor}`}>
                              {urgencyText}
                            </div>

                            {/* Main Content */}
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-3">
                                <div className="p-2 bg-orange-500/20 rounded-lg">
                                  <AlertTriangle className="w-5 h-5 text-orange-400" />
                                </div>
                                <div>
                                  <h3 className="text-lg font-semibold text-white">
                                    Empty Slot Alert
                                  </h3>
                                  <p className="text-sm text-gray-400">
                                    Team: <span className="text-white font-medium">{notification.team_name}</span>
                                  </p>
                                </div>
                              </div>

                              {/* Slot Details */}
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                                <div className="flex items-center gap-2">
                                  <Calendar className="w-4 h-4 text-blue-400" />
                                  <div>
                                    <p className="text-sm text-gray-400">Date</p>
                                    <p className="text-white font-medium">{startTime.date}</p>
                                  </div>
                                </div>
                                
                                <div className="flex items-center gap-2">
                                  <Clock className="w-4 h-4 text-green-400" />
                                  <div>
                                    <p className="text-sm text-gray-400">Start Time</p>
                                    <p className="text-white font-medium">{startTime.time}</p>
                                  </div>
                                </div>

                                <div className="flex items-center gap-2">
                                  <Clock className="w-4 h-4 text-red-400" />
                                  <div>
                                    <p className="text-sm text-gray-400">End Time</p>
                                    <p className="text-white font-medium">{endTime.time}</p>
                                  </div>
                                </div>
                              </div>

                              {/* Time Warning */}
                              <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-3">
                                <div className="flex items-center gap-2">
                                  <Clock className="w-4 h-4 text-orange-400" />
                                  <p className="text-orange-200 text-sm">
                                    <span className="font-semibold">{notification.hours_from_now}h</span> remaining until this slot starts
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex flex-col gap-2">
                            <button
                              onClick={() => handleMarkAsRead(notification.slot_id)}
                              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all text-sm font-medium"
                            >
                              <Check className="w-4 h-4" />
                              Mark as Read
                            </button>
                            {/* Only show Assign User button if slot is actually empty */}
                            {notification.is_empty !== false && (
                              <button
                                onClick={() => handleManageSlot(notification)}
                                disabled={loadingUsers}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white rounded-lg transition-all text-sm font-medium"
                              >
                                <UserPlus className="w-4 h-4" />
                                {loadingUsers ? "Loading..." : "Assign User"}
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Assign User Modal */}
      {assignSlotModalOpen && selectedSlot && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Assign User to Slot</h2>
                  <div className="mt-2 text-sm text-gray-600">
                    <p><strong>Team:</strong> {selectedSlot.team_name}</p>
                    <p><strong>Date:</strong> {new Date(selectedSlot.start_time).toLocaleDateString('en-US', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}</p>
                    <p><strong>Time:</strong> {new Date(selectedSlot.start_time).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true
                    })} - {new Date(selectedSlot.end_time).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true
                    })}</p>
                  </div>
                </div>
                <button
                  onClick={closeAssignModal}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-6 h-6 text-gray-500" />
                </button>
              </div>
            </div>

            <div className="p-6 max-h-96 overflow-y-auto">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Users</h3>
              
              {loadingUsers ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  <span className="ml-2 text-gray-600">Loading available users...</span>
                </div>
              ) : availableUsers.length > 0 ? (
                <div className="space-y-3">
                  {availableUsers.map((user) => (
                    <div
                      key={user.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                          {user.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{user.name}</div>
                          <div className="text-sm text-gray-600">{user.email}</div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleAssignUser(user.id)}
                        disabled={assigningUser}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white rounded-lg transition-all text-sm font-medium flex items-center gap-2"
                      >
                        {assigningUser ? (
                          <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            Assigning...
                          </>
                        ) : (
                          <>
                            <UserPlus className="w-4 h-4" />
                            Assign
                          </>
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No available users found for this slot.</p>
                  <p className="text-sm mt-1">All team members may be on leave for this date.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
