"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  UploadCloud,
  Activity,
  PhoneCall,
  CheckCircle,
  AlertTriangle,
  Clock,
  FileText,
  User,
  Stethoscope,
  Calendar
} from "lucide-react";

export default function Home() {
  const [patients, setPatients] = useState<any[]>([]);
  const [consultations, setConsultations] = useState<any[]>([]);
  const [callLogs, setCallLogs] = useState<any[]>([]);

  // Form state
  const [patientId, setPatientId] = useState("");
  const [followUpDate, setFollowUpDate] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // Tab state: "dashboard" | "upload" | "logs"
  const [activeTab, setActiveTab] = useState("dashboard");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const pRes = await fetch("http://localhost:8000/doctor/patients");
      if (pRes.ok) setPatients(await pRes.json());

      const cRes = await fetch("http://localhost:8000/doctor/consultations");
      if (cRes.ok) setConsultations(await cRes.json());

      const lRes = await fetch("http://localhost:8000/doctor/call-logs");
      if (lRes.ok) setCallLogs(await lRes.json());
    } catch (e) {
      console.error("Failed to fetch data", e);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !patientId || !followUpDate) return alert("Please fill all fields");

    setUploading(true);
    const formData = new FormData();
    formData.append("patient_id", patientId);
    formData.append("doctor_id", "dr_123");
    formData.append("follow_up_date", new Date(followUpDate).toISOString());
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/upload/consultation", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        alert("Consultation uploaded & scheduled successfully!");
        setFile(null);
        setPatientId("");
        setFollowUpDate("");
        setActiveTab("dashboard");
        fetchData();
      } else {
        const err = await res.json();
        alert("Error: " + JSON.stringify(err));
      }
    } catch (error) {
      alert("Error connecting to server.");
    } finally {
      setUploading(false);
    }
  };

  const markResolved = async (consultationId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/doctor/consultations/${consultationId}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "completed" })
      });
      if (res.ok) {
        fetchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Helpers
  const getPatientName = (id: string) => {
    const p = patients.find(p => p.id === id);
    return p ? p.name : id.slice(0, 8);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'escalated':
        return <span className="flex items-center gap-1 bg-red-500/20 text-red-400 px-3 py-1 rounded-full text-xs font-bold border border-red-500/30"><AlertTriangle size={12} /> ESCALATED</span>;
      case 'completed':
        return <span className="flex items-center gap-1 bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full text-xs font-bold border border-emerald-500/30"><CheckCircle size={12} /> COMPLETED</span>;
      case 'pending':
      default:
        return <span className="flex items-center gap-1 bg-amber-500/20 text-amber-400 px-3 py-1 rounded-full text-xs font-bold border border-amber-500/30"><Clock size={12} /> PENDING</span>;
    }
  };

  const getUrgencyColor = (level: string) => {
    if (!level) return "text-slate-400";
    const l = level.toLowerCase();
    if (l.includes("high")) return "text-red-400 font-bold";
    if (l.includes("med")) return "text-amber-400 font-bold";
    return "text-emerald-400 font-bold";
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 font-sans selection:bg-indigo-500/30">

      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-[#020617]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Activity className="text-white" size={20} />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent tracking-tight">
                AuraHealth
              </h1>
              <p className="text-[10px] uppercase tracking-widest text-indigo-400 font-semibold">AI Triage Dashboard</p>
            </div>
          </div>

          <div className="flex space-x-1 bg-slate-900/50 p-1 rounded-2xl border border-white/5">
            {['dashboard', 'upload', 'logs'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`relative px-6 py-2.5 rounded-xl text-sm font-medium transition-colors ${activeTab === tab ? "text-white" : "text-slate-400 hover:text-slate-200"}`}
              >
                {activeTab === tab && (
                  <motion.div
                    layoutId="active-tab"
                    className="absolute inset-0 bg-slate-800 rounded-xl border border-white/10"
                    initial={false}
                    transition={{ type: "spring", stiffness: 500, damping: 35 }}
                  />
                )}
                <span className="relative z-10 capitalize flex items-center gap-2">
                  {tab === 'dashboard' && <Activity size={16} />}
                  {tab === 'upload' && <UploadCloud size={16} />}
                  {tab === 'logs' && <PhoneCall size={16} />}
                  {tab === 'logs' ? 'Call Logs' : tab}
                </span>
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-semibold text-slate-200">Dr. Sarah Jenkins</p>
              <p className="text-xs text-slate-500">Chief of Cardiology</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center">
              <User size={18} className="text-slate-400" />
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <AnimatePresence mode="wait">

          {/* DASHBOARD TAB */}
          {activeTab === "dashboard" && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-8"
            >
              <div className="flex items-end justify-between mb-8">
                <div>
                  <h2 className="text-3xl font-bold tracking-tight text-white mb-2">Active Consultations</h2>
                  <p className="text-slate-400">Manage patient follow-ups and review AI triage escalations.</p>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4">
                {consultations.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-24 bg-slate-900/30 rounded-3xl border border-white/5 border-dashed">
                    <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
                      <FileText className="text-slate-500" size={24} />
                    </div>
                    <p className="text-slate-400 text-lg">No consultations scheduled.</p>
                  </div>
                )}
                {consultations.map(c => {
                  const patientName = getPatientName(c.patient_id);
                  return (
                    <div key={c.id} className="group relative bg-slate-900/40 hover:bg-slate-900/80 backdrop-blur-sm border border-white/5 hover:border-white/10 rounded-2xl p-6 transition-all duration-300">

                      {/* Left glow effect on hover */}
                      <div className={`absolute top-0 left-0 w-1 h-full rounded-l-2xl transition-colors duration-300 
                        ${c.status === 'escalated' ? 'bg-red-500 shadow-[0_0_15px_rgba(239,68,68,0.5)]' :
                          c.status === 'completed' ? 'bg-emerald-500' : 'bg-transparent group-hover:bg-indigo-500'}
                      `} />

                      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 pl-4">
                        <div className="flex-1 space-y-3">
                          <div className="flex items-center gap-4">
                            <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                              {patientName}
                            </h3>
                            {getStatusBadge(c.status)}
                          </div>
                          <div className="flex flex-wrap items-center gap-6 text-sm text-slate-400">
                            <span className="flex items-center gap-1.5"><Calendar size={14} /> Due: {new Date(c.follow_up_date).toLocaleDateString()}</span>
                            <span className="flex items-center gap-1.5"><Stethoscope size={14} /> Original Consult ID: <span className="font-mono text-xs">{c.id.split("-")[0]}</span></span>
                          </div>
                          <div className="bg-slate-950/50 rounded-xl p-4 text-sm text-slate-300 border border-white/5 leading-relaxed">
                            {c.summary_text.length > 200 ? c.summary_text.slice(0, 200) + "..." : c.summary_text}
                          </div>
                        </div>

                        {/* Action buttons */}
                        <div className="shrink-0 flex flex-col gap-3 min-w-[140px]">
                          {c.status === 'escalated' && (
                            <button
                              onClick={() => markResolved(c.id)}
                              className="w-full bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 py-2.5 px-4 rounded-xl text-sm font-semibold transition flex items-center justify-center gap-2"
                            >
                              <CheckCircle size={16} /> Resolve
                            </button>
                          )}
                          <button className="w-full bg-white/5 hover:bg-white/10 text-white border border-white/5 hover:border-white/10 py-2.5 px-4 rounded-xl text-sm font-medium transition">
                            View Details
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}

          {/* UPLOAD TAB */}
          {activeTab === "upload" && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="max-w-2xl mx-auto"
            >
              <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-3xl p-8 sm:p-10 shadow-2xl relative overflow-hidden">
                <div className="absolute -top-24 -right-24 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"></div>

                <div className="mb-8">
                  <div className="w-12 h-12 bg-indigo-500/20 text-indigo-400 rounded-2xl flex items-center justify-center mb-6 border border-indigo-500/30">
                    <UploadCloud size={24} />
                  </div>
                  <h2 className="text-3xl font-bold text-white mb-2">New Consultation</h2>
                  <p className="text-slate-400">Upload PDF reports to queue them for the AI voice agent follow-up.</p>
                </div>

                <form onSubmit={handleUpload} className="space-y-6 relative z-10">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Select Patient</label>
                    <div className="relative">
                      <select
                        value={patientId}
                        onChange={(e) => setPatientId(e.target.value)}
                        className="w-full bg-slate-950/50 border border-white/10 rounded-xl py-3.5 px-4 text-slate-200 appearance-none outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                        required
                      >
                        <option value="" disabled>Choose a patient from your roster...</option>
                        {patients.map(p => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                        <option value="NEW_PATIENT_UUID_MOCK">Mock New Patient</option>
                      </select>
                      <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">▼</div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Follow-up Date</label>
                    <input
                      type="date"
                      value={followUpDate}
                      onChange={(e) => setFollowUpDate(e.target.value)}
                      className="w-full bg-slate-950/50 border border-white/10 rounded-xl py-3.5 px-4 text-slate-200 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition [color-scheme:dark]"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Medical Report (PDF)</label>
                    <div className="relative group cursor-pointer">
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                        required
                      />
                      <div className="w-full flex items-center justify-between bg-slate-950/50 border border-white/10 group-hover:border-indigo-500/50 border-dashed rounded-xl py-6 px-6 transition">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-slate-800 rounded-full flex items-center justify-center text-slate-400 group-hover:text-indigo-400 transition">
                            <FileText size={20} />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-slate-200">
                              {file ? file.name : "Browse or drop file"}
                            </p>
                            <p className="text-xs text-slate-500">{file ? (file.size / 1024).toFixed(1) + " KB" : "PDF up to 10MB"}</p>
                          </div>
                        </div>
                        {!file && <div className="text-sm font-medium text-indigo-400 bg-indigo-500/10 px-4 py-2 rounded-lg">Upload</div>}
                      </div>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={uploading}
                    className="w-full group mt-4 bg-white hover:bg-slate-100 text-slate-900 font-semibold py-4 px-6 rounded-xl shadow-xl transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {uploading ? "Extracting & Embedding..." : "Queue AI Follow-up"}
                  </button>
                </form>
              </div>
            </motion.div>
          )}

          {/* CALL LOGS TAB */}
          {activeTab === "logs" && (
            <motion.div
              key="logs"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-8"
            >
              <div>
                <h2 className="text-3xl font-bold tracking-tight text-white mb-2">AI Call Logs</h2>
                <p className="text-slate-400">Review transcripts and AI-generated summaries of patient interactions.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {callLogs.length === 0 && (
                  <div className="col-span-1 md:col-span-2 flex flex-col items-center justify-center py-20 bg-slate-900/30 rounded-3xl border border-white/5 border-dashed text-slate-400">
                    <PhoneCall className="mb-4 opacity-50" size={32} />
                    <p>No phone calls have been made yet.</p>
                  </div>
                )}
                {callLogs.map(log => {
                  return (
                    <div key={log.id} className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 flex flex-col h-full hover:border-white/10 transition">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center bg-slate-950 border border-white/5 ${getUrgencyColor(log.urgency_level)}`}>
                            <PhoneCall size={18} />
                          </div>
                          <div>
                            <p className="font-semibold text-white">Consultation <span className="font-mono text-xs text-slate-400 ml-1">#{log.consultation_id.slice(0, 6)}</span></p>
                            <p className="text-xs text-slate-500">{new Date(log.created_at).toLocaleString()}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1">Urgency</p>
                          <p className={`text-sm ${getUrgencyColor(log.urgency_level)}`}>{log.urgency_level ? log.urgency_level.toUpperCase() : "UNKNOWN"}</p>
                        </div>
                      </div>

                      <div className="flex-1 space-y-4">
                        <div>
                          <p className="text-xs text-indigo-400 uppercase font-bold tracking-wider mb-2">AI Summary</p>
                          <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-xl p-4 text-sm text-slate-300 leading-relaxed">
                            {log.ai_summary || "No summary generated."}
                          </div>
                        </div>

                        <div>
                          <p className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-2">Raw Transcript</p>
                          <div className="bg-slate-950/50 border border-white/5 rounded-xl p-4 text-xs text-slate-400 h-24 overflow-y-auto leading-relaxed font-mono">
                            {log.transcript || "[Empty Transcript]"}
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center text-xs text-slate-500">
                        <span>Duration: {log.call_duration || 0}s</span>
                        <span>Status: {log.call_status}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </main>
    </div>
  );
}

