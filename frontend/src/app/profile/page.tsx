"use client";

import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { updateUserProfile, exportGDPRData, requestGDPRErasure } from "../../lib/api";
import {
  User as UserIcon,
  Shield,
  Eye,
  CheckCircle,
  AlertCircle,
  Save,
  Lock,
  Sparkles,
  Sliders,
} from "lucide-react";

export default function UserProfilePage() {
  const { user, refreshUser, logout, a11y, updateA11y } = useAuth();
  const [firstName, setFirstName] = useState(user?.first_name || "");
  const [lastName, setLastName] = useState(user?.last_name || "");
  const [bio, setBio] = useState(user?.bio || "");
  const [marketingConsent, setMarketingConsent] = useState(user?.marketing_consent || false);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // GDPR State
  const [isExporting, setIsExporting] = useState(false);
  const [showErasureModal, setShowErasureModal] = useState(false);
  const [erasurePassword, setErasurePassword] = useState("");
  const [isErasing, setIsErasing] = useState(false);

  const handleExportData = async () => {
    setIsExporting(true);
    try {
      const data = await exportGDPRData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `gdpr_export_${user?.id || "data"}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setStatusMessage({ type: "success", text: "GDPR data archive generated and downloaded." });
    } catch (err) {
      console.error("GDPR export error", err);
      setStatusMessage({ type: "error", text: "Failed to export data archive." });
    } finally {
      setIsExporting(false);
    }
  };

  const handleConfirmErasure = async () => {
    if (!erasurePassword) return;
    setIsErasing(true);
    try {
      await requestGDPRErasure(erasurePassword);
      alert("Your account personal data has been erased in accordance with GDPR Art. 17. You will now be logged out.");
      logout();
    } catch (err: any) {
      alert(err.response?.data?.error || "Failed to process account erasure.");
    } finally {
      setIsErasing(false);
      setShowErasureModal(false);
      setErasurePassword("");
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatusMessage(null);
    try {
      await updateUserProfile({
        first_name: firstName,
        last_name: lastName,
        bio,
        marketing_consent: marketingConsent,
      });
      await refreshUser();
      setStatusMessage({ type: "success", text: "Profile & preferences saved successfully." });
    } catch (err) {
      setStatusMessage({ type: "error", text: "Failed to update profile. Please try again." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Account Settings & Preferences
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Manage your personal details, legally recorded GDPR consents, and WCAG accessibility parameters.
        </p>
      </div>

      {statusMessage && (
        <div
          role="alert"
          className={`p-4 rounded-xl flex items-center space-x-2 text-xs font-semibold ${
            statusMessage.type === "success"
              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
              : "bg-rose-50 text-rose-800 border border-rose-200"
          }`}
        >
          {statusMessage.type === "success" ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Main Profile Form */}
      <form onSubmit={handleSaveProfile} className="card bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs space-y-6">
        <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2 pb-3 border-b border-slate-100">
          <UserIcon className="w-5 h-5 text-indigo-600" />
          <span>Personal Information</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Email Address (Immutable)</label>
            <input
              type="text"
              disabled
              value={user?.email || ""}
              className="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 cursor-not-allowed font-mono"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Platform Role</label>
            <div className="flex items-center space-x-2 py-2">
              <span className="font-bold uppercase tracking-wider text-[11px] px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                {user?.role || "LEARNER"}
              </span>
              <span className="text-slate-400">· Server RBAC enforced</span>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">First Name</label>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Last Name</label>
            <input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="sm:col-span-2">
            <label className="block font-semibold text-slate-700 mb-1">Professional / Academic Bio</label>
            <textarea
              rows={3}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Tell instructors and fellow learners about your background..."
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* GDPR Consent Ledger (FR-AUTH-05) */}
        <div className="pt-6 border-t border-slate-100 space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
            <Shield className="w-5 h-5 text-indigo-600" />
            <span>GDPR Consent Ledger & Data Privacy (FR-AUTH-05)</span>
          </h2>

          <div className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-800">Terms of Service Acceptance</p>
                <p className="text-slate-500 text-[11px]">Legally binding educational contract</p>
              </div>
              <span className="inline-flex items-center space-x-1 font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Recorded</span>
              </span>
            </div>

            <div className="flex items-center justify-between border-t border-slate-200/60 pt-3">
              <div>
                <p className="font-semibold text-slate-800">Privacy Policy Acceptance</p>
                <p className="text-slate-500 text-[11px]">Data processing & storage disclosures</p>
              </div>
              <span className="inline-flex items-center space-x-1 font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Recorded</span>
              </span>
            </div>

            <div className="flex items-center justify-between border-t border-slate-200/60 pt-3">
              <div>
                <p className="font-semibold text-slate-800">Optional Learning Analytics Processing</p>
                <p className="text-slate-500 text-[11px]">Permits skill mastery recommendations & adaptive pathways</p>
              </div>
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={marketingConsent}
                  onChange={(e) => setMarketingConsent(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Accessibility & Display Preferences (NFR-A11Y-01) */}
        <div className="pt-6 border-t border-slate-100 space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
            <Eye className="w-5 h-5 text-indigo-600" />
            <span>Accessibility & Visual Display (WCAG 2.1 AA)</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <p className="font-semibold text-slate-800">High Contrast Mode</p>
              <p className="text-slate-500 text-[11px]">Strict 7:1 color contrast for low-vision readability</p>
              <button
                type="button"
                onClick={() =>
                  updateA11y({
                    contrastMode: a11y.contrastMode === "high" ? "normal" : "high",
                  })
                }
                className={`px-3 py-1.5 rounded-lg font-semibold text-xs transition border ${
                  a11y.contrastMode === "high"
                    ? "bg-indigo-600 text-white border-indigo-700"
                    : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100"
                }`}
              >
                {a11y.contrastMode === "high" ? "High Contrast Active" : "Enable High Contrast"}
              </button>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <p className="font-semibold text-slate-800">Text Scaling</p>
              <p className="text-slate-500 text-[11px]">Responsive rem-based font sizing</p>
              <div className="grid grid-cols-3 gap-1">
                {(["normal", "large", "xlarge"] as const).map((sz) => (
                  <button
                    key={sz}
                    type="button"
                    onClick={() => updateA11y({ fontSize: sz })}
                    className={`py-1 rounded text-center font-medium border text-[11px] ${
                      a11y.fontSize === sz
                        ? "bg-indigo-600 text-white border-indigo-700"
                        : "bg-white text-slate-700 border-slate-200"
                    }`}
                  >
                    {sz === "normal" ? "100%" : sz === "large" ? "112%" : "125%"}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="pt-4 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700 transition shadow-xs text-xs flex items-center space-x-2 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? "Saving Changes..." : "Save Preferences"}</span>
          </button>
        </div>
      </form>

      {/* GDPR Data Subject Rights (FR-PRV-01 & FR-PRV-02) */}
      <div className="card bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs space-y-6">
        <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2 pb-3 border-b border-slate-100">
          <Shield className="w-5 h-5 text-indigo-600" />
          <span>GDPR Data Portability & Account Erasure</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          {/* Export Data (Art. 20) */}
          <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-3 flex flex-col justify-between">
            <div className="space-y-1">
              <h3 className="font-bold text-slate-800 text-sm">Download My Data (Portability)</h3>
              <p className="text-slate-500 leading-relaxed text-[11px]">
                Export a machine-readable JSON archive containing your full profile, consent ledger, enrolled course progress, assessment submissions, and discussion posts.
              </p>
            </div>
            <button
              type="button"
              onClick={handleExportData}
              disabled={isExporting}
              className="px-4 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold rounded-lg border border-indigo-200 text-xs transition flex items-center justify-center space-x-2"
            >
              <span>{isExporting ? "Compiling Archive..." : "Download JSON Archive"}</span>
            </button>
          </div>

          {/* Erase Account (Art. 17) */}
          <div className="p-5 rounded-xl bg-rose-50/50 border border-rose-200 space-y-3 flex flex-col justify-between">
            <div className="space-y-1">
              <h3 className="font-bold text-rose-900 text-sm">Right to Erasure (Forget Me)</h3>
              <p className="text-rose-700/80 leading-relaxed text-[11px]">
                Permanently pseudonymize and erase all personal identifying information (PII) from FutureLearning. Historical audit logs will record the erasure in accordance with GDPR Art. 17.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowErasureModal(true)}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-lg text-xs transition flex items-center justify-center space-x-2"
            >
              <span>Request Account Erasure</span>
            </button>
          </div>
        </div>
      </div>

      {/* Erasure Confirmation Modal */}
      {showErasureModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center space-x-3 text-rose-600">
              <AlertCircle className="w-6 h-6 shrink-0" />
              <h3 className="font-bold text-base text-slate-900">Confirm GDPR Account Erasure</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              This action is <strong className="text-rose-600">permanent and irreversible</strong>. Your personal data, email, and credentials will be deleted and converted to anonymized placeholders.
            </p>
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700">Enter your password to confirm:</label>
              <input
                type="password"
                value={erasurePassword}
                onChange={(e) => setErasurePassword(e.target.value)}
                placeholder="Current password"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-500"
              />
            </div>
            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setShowErasureModal(false);
                  setErasurePassword("");
                }}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmErasure}
                disabled={isErasing || !erasurePassword}
                className="px-4 py-2 rounded-lg text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white disabled:opacity-50"
              >
                {isErasing ? "Erasing Data..." : "Permanently Erase"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

