import React, { useEffect, useState } from "react";
import { Eye, EyeOff, Calendar, Clock, CheckCircle2, Sparkles } from "lucide-react";

import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { setUserDetails } from "../../store/UserDetailsSlice";
import { toast } from "react-toastify";
import { loginRoute} from "../../services/userService";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const dispatch = useDispatch();

  const navigate = useNavigate();
  const [errorsFromBackend, setErrorsFromBackend] = useState({
    email: [],
    password: [],
    commonError: "",
  });

  const loginSubmitHandler = async (e) => {
    e.preventDefault();
    try {
      const response = await loginRoute(email, password)
      // setting the user details in redux store
      const userDetails = response.data.user;

      // Check if user is active first
      if (!userDetails.is_active) {
        toast.error("User is blocked", { position: "bottom-center" });
        return;
      }

      // User is active, proceed with login
      dispatch(setUserDetails(userDetails));

      toast.success("Login Successful.", {
        position: "bottom-center",
      });

      // Check if user is manager to determine navigation
      if (userDetails.is_manager) {
        navigate("/admin_home_page");
      } else {
        navigate("/user/home");
      }

    } catch (error) {
      toast.error("Unable to login.", {
        position: "bottom-center",
      });
      if (error.response && error.response.data && error.response.data.error) {
        setErrorsFromBackend(error.response.data.error);
      } else {
        setErrorsFromBackend({
          email: [],
          password: [],
          commonError: "Something went wrong. Please try again later.",
        });
      }
    }
  };

  return (
    <div className="min-h-screen h-screen w-screen min-w-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center relative overflow-hidden">
      {/* Animated gradient orbs */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse delay-700"></div>
      <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse delay-1000"></div>

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:100px_100px]"></div>

      {/* Main Content */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 flex items-center justify-between gap-12">
        {/* Left Side - Feature Showcase */}
        <div className="flex-1 hidden lg:block">
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl shadow-lg shadow-purple-500/50">
                <Calendar className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-5xl font-bold text-white">
                TimeSync
              </h1>
            </div>
            <p className="text-2xl text-gray-300 mb-3">
              Smart Scheduling for Modern Teams
            </p>
            <p className="text-lg text-gray-400 max-w-xl">
              Experience effortless time management with AI-powered scheduling, seamless integrations, and beautiful calendar views.
            </p>
          </div>

          {/* Feature Cards */}
          <div className="space-y-4">
            <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-2xl">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl shadow-lg">
                  <Clock className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Smart Time Blocking</h3>
                  <p className="text-gray-300">Automatically organize your day with intelligent scheduling algorithms.</p>
                </div>
              </div>
            </div>

            <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-2xl">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl shadow-lg">
                  <CheckCircle2 className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Team Coordination</h3>
                  <p className="text-gray-300">Find perfect meeting times across multiple calendars instantly.</p>
                </div>
              </div>
            </div>

            <div className="backdrop-blur-xl bg-white/10 rounded-2xl p-6 border border-white/20 shadow-2xl">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-gradient-to-br from-pink-500 to-rose-500 rounded-xl shadow-lg">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Beautiful Interface</h3>
                  <p className="text-gray-300">Enjoy a premium, intuitive design that makes scheduling delightful.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="w-full max-w-md lg:max-w-lg">
          <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl p-8 lg:p-12 border border-white/20 relative overflow-hidden">
            {/* Glossy overlay effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>

            {/* Logo for mobile */}
            <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl shadow-lg">
                <Calendar className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-white">TimeSync</h1>
            </div>

            {/* Header */}
            <div className="text-center mb-8 relative z-10">
              <h2 className="text-4xl font-bold text-white mb-3 bg-clip-text text-transparent bg-gradient-to-r from-white via-purple-200 to-white">
                Welcome Back
              </h2>
              <p className="text-gray-300 text-lg">
                Sign in to continue to your dashboard
              </p>
            </div>

            {/* Form */}
            <form onSubmit={loginSubmitHandler} className="space-y-6 relative z-10">
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-white mb-3">
                  Email Address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-5 py-4 bg-white/10 backdrop-blur-sm border border-white/30 rounded-2xl text-white placeholder-gray-400 focus:bg-white/20 focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:outline-none transition-all duration-300 shadow-lg"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-white mb-3">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-5 py-4 bg-white/10 backdrop-blur-sm border border-white/30 rounded-2xl text-white placeholder-gray-400 focus:bg-white/20 focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:outline-none transition-all duration-300 shadow-lg"
                    placeholder="••••••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-300 hover:text-white transition-colors"
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>
              <button 
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 via-purple-500 to-blue-500 hover:from-purple-500 hover:via-purple-400 hover:to-blue-400 text-white py-4 px-6 rounded-2xl font-bold text-lg shadow-2xl shadow-purple-500/50 hover:shadow-purple-400/60 focus:outline-none focus:ring-4 focus:ring-purple-500/50 transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 relative overflow-hidden group"
              >
                <span className="relative z-10">Sign In</span>
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-700"></div>
              </button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/20"></div>
                </div>
               
              </div>

              <p className="text-center text-gray-300 text-sm">
                Don't have an account?{" "}
                <button className="font-semibold text-purple-300 hover:text-purple-200 transition-colors">
                  Sign up free
                </button>
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
