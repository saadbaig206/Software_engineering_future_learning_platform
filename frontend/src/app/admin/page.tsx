"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AdminPlatformOverview } from "../../lib/types";
import { getAdminPlatformOverview } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import {
  ShieldAlert,
  Users,
  BookOpen,
  Activity,
  Clock,
  CheckCircle2,
  FileText,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  Lock,
} from "lucide-react";

export default function AdminGovernancePage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();

  const [overview, setOverview] = useState<AdminPlatformOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAdminPlatformOverview();
      setOverview(data);
    } catch (err: any) {
      console.error("Failed to load admin overview:", err);
      setError(
        err.response?.data?.detail || "Admin access required to view platform overview."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!user || user.role !== "ADMIN") {
        setError("Administrator privileges are required to view this panel.");
        setLoading(false);
        return;
      }
      fetchOverview();
    }
  }, [authLoading, user]);

  if (authLoading || (loading && !overview)) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="flex items-center space-x-3 text-sm text-slate-400">
          <RefreshCw className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Loading governance metrics and audit log...</span>
        </div>
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex flex-col items-center justify-center space-y-4">
        <Lock className="w-12 h-12 text-rose-500" />
        <h1 className="text-xl font-bold text-white">Access Denied</h1>
        <p className="text-sm text-slate-400 max-w-md text-center">{error}</p>
        <Link
          href="/"
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-lg text-white"
        >
          Return to Home
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-xs px-6 py-4 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-10">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center border border-rose-500/20">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-rose-500/20 text-rose-300">
                Governance & Security Admin
              </span>
              <span className="text-xs text-slate-400">· FutureLearning Engine</span>
            </div>
            <h1 className="text-lg font-bold text-white mt-0.5">Platform Administration</h1>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            href="/smoke-test"
            className="px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition"
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Subsystem Health & Smoke Tests</span>
          </Link>
          <button
            onClick={fetchOverview}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6 space-y-8">
        {/* KPI Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Total Users */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400">Total Users</span>
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-black text-white">{overview.total_users}</div>
              <div className="flex flex-wrap gap-1.5 text-2xs pt-1">
                {Object.entries(overview.users_by_role).map(([role, count]) => (
                  <span
                    key={role}
                    className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-mono"
                  >
                    {role}: {count}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Card 2: 30-Day Active Learners */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400">30-Day Active</span>
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-black text-white">{overview.active_users_30d}</div>
              <p className="text-xs text-slate-400">
                Engaged learners in past month
              </p>
            </div>
          </div>

          {/* Card 3: Courses & Published */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400">Curriculum Scope</span>
              <div className="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center">
                <BookOpen className="w-4 h-4" />
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-black text-white">
                {overview.published_courses} / {overview.total_courses}
              </div>
              <p className="text-xs text-slate-400">
                Courses published to live catalog
              </p>
            </div>
          </div>

          {/* Card 4: Learning Hours */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400">Cumulative Time</span>
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-black text-white">
                {overview.estimated_learning_hours} hrs
              </div>
              <p className="text-xs text-slate-400">
                {overview.completed_enrollments} of {overview.total_enrollments} enrollments finished ({overview.platform_completion_rate}%)
              </p>
            </div>
          </div>
        </div>

        {/* Section 2: Recent Governance Audit Trail */}
        <section className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span>Security & Governance Audit Log</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Immutable compliance audit trail tracking logins, course publications, moderation actions, and GDPR subject rights.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-medium">
                  <th className="pb-3 pr-4">Timestamp</th>
                  <th className="pb-3 px-4">Actor</th>
                  <th className="pb-3 px-4">Action</th>
                  <th className="pb-3 px-4">Target Entity</th>
                  <th className="pb-3 pl-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {overview.recent_audit_logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-slate-500 text-xs">
                      No audit events logged yet.
                    </td>
                  </tr>
                ) : (
                  overview.recent_audit_logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/30 transition font-mono">
                      <td className="py-3 pr-4 text-slate-400">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-slate-200">
                        {log.actor_email}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-2xs font-bold ${
                            log.action.includes("GDPR")
                              ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                              : log.action.includes("PUBLISH")
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : "bg-slate-800 text-slate-300 border border-slate-700"
                          }`}
                        >
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {log.target_model ? `${log.target_model}:${log.target_id.slice(0, 8)}` : "—"}
                      </td>
                      <td className="py-3 pl-4 text-right text-emerald-400 text-2xs">
                        RECORDED ✓
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
