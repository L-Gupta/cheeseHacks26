"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [patients, setPatients] = useState<any[]>([]);
  const [consultations, setConsultations] = useState<any[]>([]);

  // Form state
  const [patientId, setPatientId] = useState("");
  const [followUpDate, setFollowUpDate] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const pRes = await fetch("http://localhost:8000/doctor/patients");
      if (pRes.ok) setPatients(await pRes.json());

      const cRes = await fetch("http://localhost:8000/doctor/consultations");
      if (cRes.ok) setConsultations(await cRes.json());
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
        alert("Consultation uploaded & embedded successfully!");
        setFile(null);
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-12">
        <header className="flex justify-between items-center border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
              AI Patient Follow-up
            </h1>
            <p className="text-slate-400 mt-2">Doctor Dashboard & Triage Center</p>
          </div>
          <div className="text-right">
            <div className="bg-slate-900 px-4 py-2 rounded-full border border-slate-700 text-sm font-medium">
              Dr. John Doe
            </div>
          </div>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Upload Widget */}
          <section className="col-span-1 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl"></div>
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              Upload Consultation
            </h2>

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Patient</label>
                <select
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 outline-none focus:border-indigo-500 transition"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                  <option value="NEW_PATIENT_UUID_MOCK">Mock New Patient</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-1">Follow-up Date</label>
                <input
                  type="date"
                  value={followUpDate}
                  onChange={(e) => setFollowUpDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 outline-none focus:border-indigo-500 transition"
                  required
                />
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-1">Consultation Report (PDF)</label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-500/10 file:text-indigo-400 hover:file:bg-indigo-500/20 cursor-pointer transition border border-slate-700 rounded-xl p-2 bg-slate-950"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={uploading}
                className="w-full mt-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold py-3 px-6 rounded-xl shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? "Processing & Embedding..." : "Schedule Follow-up"}
              </button>
            </form>
          </section>

          {/* Activity Section */}
          <section className="col-span-1 lg:col-span-2 space-y-6">
            <h2 className="text-xl font-semibold px-2">Scheduled Follow-ups</h2>
            <div className="grid grid-cols-1 gap-4">
              {consultations.length === 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-slate-500">
                  No consultations scheduled yet.
                </div>
              )}
              {consultations.map(c => (
                <div key={c.id} className="bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-2xl p-5 shadow-md transition group">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <p className="font-medium text-slate-200 text-lg">Patient ID: <span className="text-slate-400 text-sm">{c.patient_id.slice(0, 8)}</span></p>
                      <p className="text-slate-400 text-sm mt-1">Status:
                        <span className={`ml-2 px-2 py-1 rounded-md text-xs font-semibold
                               ${c.status === 'pending' ? 'bg-amber-500/20 text-amber-400' : ''}
                               ${c.status === 'escalated' ? 'bg-red-500/20 text-red-400' : ''}
                               ${c.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : ''}`
                        }>
                          {c.status.toUpperCase()}
                        </span>
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-slate-400">Due Date</p>
                      <p className="text-indigo-400">{new Date(c.follow_up_date).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="bg-slate-950 rounded-lg p-3 text-sm text-slate-300 border border-slate-800 line-clamp-2">
                    {c.summary_text}
                  </div>
                </div>
              ))}
            </div>
          </section>

        </main>
      </div>
    </div>
  );
}
