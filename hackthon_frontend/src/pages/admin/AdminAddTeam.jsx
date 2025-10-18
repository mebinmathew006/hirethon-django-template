import React, { useState } from "react";
import { Users, Calendar, ArrowLeft, Clock, Zap, Shield } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function AdminAddTeam() {
  const [formData, setFormData] = useState({
    name: "",
    slot_duration_hours: "1",
    slot_duration_minutes: "0",
  });
  const navigate = useNavigate();
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });

    if (touched[name]) {
      validateField(name, value);
    }
  };

  const handleBlur = (e) => {
    const { name, value } = e.target;
    setTouched({
      ...touched,
      [name]: true,
    });
    validateField(name, value);
  };

  const validateField = (name, value) => {
    let newErrors = { ...errors };

    switch (name) {
      case "name":
        if (!value.trim()) {
          newErrors.name = "Team name is required";
        } else if (value.trim().length < 3) {
          newErrors.name = "Team name must be at least 3 characters";
        } else {
          delete newErrors.name;
        }
        break;

      case "slot_duration_hours":
      case "slot_duration_minutes":
        const hours = parseInt(formData.slot_duration_hours) || 0;
        const minutes = parseInt(name === "slot_duration_minutes" ? value : formData.slot_duration_minutes) || 0;
        
        if (hours === 0 && minutes === 0) {
          newErrors.slot_duration = "Slot duration must be greater than 0";
        } else {
          delete newErrors.slot_duration;
        }
        break;

      default:
        break;
    }
    setErrors(newErrors);
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = "Team name is required";
    } else if (formData.name.trim().length < 3) {
      newErrors.name = "Team name must be at least 3 characters";
    }

    const hours = parseInt(formData.slot_duration_hours) || 0;
    const minutes = parseInt(formData.slot_duration_minutes) || 0;
    
    if (hours === 0 && minutes === 0) {
      newErrors.slot_duration = "Slot duration must be greater than 0";
    }

    setErrors(newErrors);

    const touchedFields = {};
    Object.keys(formData).forEach((key) => {
      touchedFields[key] = true;
    });
    setTouched(touchedFields);

    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    if (validateForm()) {
      const hours = parseInt(formData.slot_duration_hours) || 0;
      const minutes = parseInt(formData.slot_duration_minutes) || 0;
      const totalSeconds = (hours * 3600) + (minutes * 60);

      const teamData = {
        name: formData.name.trim(),
        slot_duration: totalSeconds,
      };

      setTimeout(() => {
        console.log("Team created:", teamData);
        setIsSubmitting(false);
      }, 2000);
    } else {
      setIsSubmitting(false);
    }
  };

  const presetDurations = [
    { label: "15 min", hours: 0, minutes: 15 },
    { label: "30 min", hours: 0, minutes: 30 },
    { label: "1 hour", hours: 1, minutes: 0 },
    { label: "2 hours", hours: 2, minutes: 0 },
  ];

  const setPresetDuration = (hours, minutes) => {
    setFormData({
      ...formData,
      slot_duration_hours: hours.toString(),
      slot_duration_minutes: minutes.toString(),
    });
    delete errors.slot_duration;
  };

  return (
    <div className="min-h-screen h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-y-auto">
      <div className="absolute top-0 left-0 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '700ms'}}></div>
      <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{animationDelay: '1000ms'}}></div>

      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:100px_100px]"></div>

      <div className="relative z-10 min-h-screen py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <button onClick={()=>navigate(-1)} className="flex items-center gap-2 text-purple-300 hover:text-purple-200 transition-colors mb-8 group">
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back to Dashboard</span>
          </button>

          <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl p-8 lg:p-12 border border-white/20 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent pointer-events-none"></div>

            <div className="relative z-10">
              <div className="flex items-center gap-4 mb-8">
                <div className="p-4 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-2xl shadow-lg shadow-blue-500/50">
                  <Users className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold text-white">Add New Team</h1>
                  <p className="text-gray-300 mt-1">Create a new team and configure scheduling settings</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-lg">
                      <Calendar className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Smart</p>
                      <p className="text-white font-semibold">Scheduling</p>
                    </div>
                  </div>
                </div>

                <div className="backdrop-blur-xl bg-white/5 rounded-xl p-4 border border-white/10">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-lg">
                      <Clock className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Flexible</p>
                      <p className="text-white font-semibold">Time Slots</p>
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
                      <p className="text-white font-semibold">Setup</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-semibold text-white mb-2">
                    Team Name *
                  </label>
                  <input
                    id="name"
                    name="name"
                    type="text"
                    value={formData.name}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    className="w-full px-4 py-4 bg-white/10 backdrop-blur-sm border border-white/30 rounded-xl text-white placeholder-gray-400 focus:bg-white/20 focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:outline-none transition-all duration-300 shadow-lg text-lg"
                    placeholder="Engineering Team Alpha"
                  />
                  {errors.name && touched.name && (
                    <p className="mt-2 text-sm text-red-300">{errors.name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-white mb-3">
                    Slot Duration *
                  </label>
                  
                  <div className="backdrop-blur-xl bg-white/5 rounded-xl p-6 border border-white/10 mb-4">
                    <p className="text-sm text-gray-300 mb-4">Quick Presets</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {presetDurations.map((preset) => (
                        <button
                          key={preset.label}
                          type="button"
                          onClick={() => setPresetDuration(preset.hours, preset.minutes)}
                          className={`py-3 px-4 rounded-xl font-semibold transition-all duration-200 ${
                            formData.slot_duration_hours === preset.hours.toString() &&
                            formData.slot_duration_minutes === preset.minutes.toString()
                              ? 'bg-gradient-to-r from-purple-600 to-blue-500 text-white shadow-lg shadow-purple-500/50'
                              : 'bg-white/10 text-gray-300 hover:bg-white/20 border border-white/20'
                          }`}
                        >
                          {preset.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="backdrop-blur-xl bg-white/5 rounded-xl p-6 border border-white/10">
                    <p className="text-sm text-gray-300 mb-4">Custom Duration</p>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="slot_duration_hours" className="block text-sm font-medium text-gray-300 mb-2">
                          Hours
                        </label>
                        <input
                          id="slot_duration_hours"
                          name="slot_duration_hours"
                          type="number"
                          min="0"
                          max="24"
                          value={formData.slot_duration_hours}
                          onChange={handleChange}
                          onBlur={handleBlur}
                          className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/30 rounded-xl text-white placeholder-gray-400 focus:bg-white/20 focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:outline-none transition-all duration-300 shadow-lg"
                          placeholder="1"
                        />
                      </div>

                      <div>
                        <label htmlFor="slot_duration_minutes" className="block text-sm font-medium text-gray-300 mb-2">
                          Minutes
                        </label>
                        <input
                          id="slot_duration_minutes"
                          name="slot_duration_minutes"
                          type="number"
                          min="0"
                          max="59"
                          value={formData.slot_duration_minutes}
                          onChange={handleChange}
                          onBlur={handleBlur}
                          className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/30 rounded-xl text-white placeholder-gray-400 focus:bg-white/20 focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:outline-none transition-all duration-300 shadow-lg"
                          placeholder="0"
                        />
                      </div>
                    </div>
                  </div>

                  {errors.slot_duration && (
                    <p className="mt-2 text-sm text-red-300">{errors.slot_duration}</p>
                  )}
                </div>

                <div className="backdrop-blur-xl bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-xl p-6 border border-purple-500/30">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg mt-1">
                      <Shield className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-white font-semibold mb-2">Team Configuration</h3>
                      <p className="text-sm text-gray-300 leading-relaxed">
                        The slot duration determines how time blocks are divided for scheduling. Choose a duration that aligns with your team's workflow and meeting preferences.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-4 pt-6">
                  <button
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                    className="flex-1 bg-gradient-to-r from-purple-600 via-purple-500 to-blue-500 hover:from-purple-500 hover:via-purple-400 hover:to-blue-400 text-white py-4 px-6 rounded-2xl font-bold text-lg shadow-2xl shadow-purple-500/50 hover:shadow-purple-400/60 focus:outline-none focus:ring-4 focus:ring-purple-500/50 transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 relative overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="relative z-10">
                      {isSubmitting ? (
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Creating Team...
                        </div>
                      ) : (
                        "Create Team"
                      )}
                    </span>
                    <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-700"></div>
                  </button>

                  <button className="px-8 py-4 bg-white/10 backdrop-blur-sm hover:bg-white/20 border border-white/30 text-white rounded-2xl font-semibold shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-white/50 transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-200">
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}