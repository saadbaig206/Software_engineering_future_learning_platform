"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { InstructorAnalytics } from "../../../../../lib/types";
import { getInstructorAnalytics } from "../../../../../lib/api";
import {
  Users,
  CheckCircle,
  GraduationCap,
  MessageSquare,
  TrendingDown,
  AlertTriangle,
  ArrowLeft,
  RefreshCw,
  Clock,
  Sparkles,
} from "lucide-react";

export default function CourseAnalyticsPage() {
  const { slug } = useParams() as { slug: string };
  const router = useRouter();

  const [analytics, setAnalytics] = useState<InstructorAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getInstructorAnalytics(slug);
      setAnalytics(data);
    } catch (err: any) {
      console.error("Failed to load course analytics:", err);
      setError(
        err.response?.data?.detail || "Unable to load analytics for this course."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (slug) fetchAnalytics();
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="flex items-center space-x-3 text-sm text-slate-400">
          <RefreshCw className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Compiling pedagogical & engagement analytics...</span>
        </div>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex flex-col items-center justify-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-rose-500" />
        <h1 className="text-xl font-bold text-white">Analytics Unavailable</h1>
        <p className="text-sm text-slate-400 max-w-md text-center">{error}</p>
        <Link
          href={`/studio/courses/${slug}`}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-lg text-white"
        >
          Return to Course Studio
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-xs px-6 py-4 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-10">
        <div className="flex items-center space-x-3">
          <Link
            href={`/studio/courses/${slug}`}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
            aria-label="Back to Course Studio"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                Course Performance Analytics
              </span>
              <span className="text-xs text-slate-400">· {analytics.course_slug}</span>
            </div>
            <h1 className="text-lg font-bold text-white mt-0.5">{analytics.course_title}</h1>
          </div>
        </div>

        <button
          onClick={fetchAnalytics}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Metrics</span>
        </button>
      </header>

      {/* Main Analytics Viewport */}
      <main className="flex-1 max-w-6xl mx-auto w-full p-6 space-y-8">
        {/* KPI Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Enrolled & Active */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400">Total Enrolled</span>
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-black text-white">{analytics.total_enrolled}</div>
              <p className="text-xs text-slate-400">
                <strong className="text-emerald-400 font-semibold">{analytics.active_students_14d} active</strong> in last 14 days
              </p>
            </div>
          </div>

          {/* Card 2: Completion Rate */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400">Completion Rate</span>
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <CheckCircle className="w-4 h-4" />
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-black text-white">
                {analytics.completion_rate_percent}%
              </div>
              <p className="text-xs text-slate-400">
                {analytics.completed_students} student{analytics.completed_students === 1 ? "" : "s"} graduated
              </p>
            </div>
          </div>

          {/* Card 3: Average Quiz Score */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400">Avg. Quiz Score</span>
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
                <GraduationCap className="w-4 h-4" />
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-black text-white">
                {analytics.avg_quiz_score_percent}%
              </div>
              <p className="text-xs text-slate-400">
                Across all checkpoint assessments
              </p>
            </div>
          </div>

          {/* Card 4: Forum Discussions */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400">Community Threads</span>
              <div className="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center">
                <MessageSquare className="w-4 h-4" />
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-black text-white">
                {analytics.total_forum_threads}
              </div>
              <p className="text-xs text-slate-400">
                Active questions & discussions
              </p>
            </div>
          </div>
        </div>

        {/* Section 2: Lesson Drop-off Funnel */}
        <section className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <TrendingDown className="w-4 h-4 text-indigo-400" />
                <span>Curriculum Drop-off Funnel</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluates learner retention through each sequential lesson. Identify bottlenecks and drop-off points.
              </p>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            {analytics.drop_off_curve.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No published lessons yet.</p>
            ) : (
              analytics.drop_off_curve.map((item, idx) => (
                <div key={item.lesson_id} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-medium truncate max-w-md">
                      {idx + 1}. {item.title} <span className="text-slate-500 text-2xs">({item.module_title})</span>
                    </span>
                    <span className="text-slate-400 text-2xs font-mono">
                      {item.completed_count} finished ({item.completion_percent_of_enrolled}%)
                    </span>
                  </div>
                  {/* Visual Bar */}
                  <div className="w-full h-2.5 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        item.completion_percent_of_enrolled >= 70
                          ? "bg-emerald-500"
                          : item.completion_percent_of_enrolled >= 40
                          ? "bg-indigo-500"
                          : "bg-amber-500"
                      }`}
                      style={{ width: `${Math.max(2, item.completion_percent_of_enrolled)}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Section 3: Difficult Questions Diagnostic */}
        <section className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Difficult Questions Diagnostic</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Identifies assessment items with the lowest student success rates to guide pedagogical remediation.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-medium">
                  <th className="pb-3 pr-4">Question Prompt</th>
                  <th className="pb-3 px-4 text-center">Attempts</th>
                  <th className="pb-3 px-4 text-center">Pass Rate</th>
                  <th className="pb-3 pl-4 text-right">Pedagogical Recommendation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {analytics.difficult_questions.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-slate-500 text-xs">
                      No assessment attempts recorded yet.
                    </td>
                  </tr>
                ) : (
                  analytics.difficult_questions.map((q) => (
                    <tr key={q.question_id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 pr-4 text-slate-200 font-medium max-w-sm">
                        {q.prompt}
                      </td>
                      <td className="py-3 px-4 text-center font-mono text-slate-400">
                        {q.total_attempts}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-2xs font-bold ${
                            q.pass_rate_percent >= 60
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                          }`}
                        >
                          {q.pass_rate_percent}%
                        </span>
                      </td>
                      <td className="py-3 pl-4 text-right text-slate-400 text-2xs">
                        {q.pass_rate_percent < 50
                          ? "Review concept explanation in lecture; clarify question distractors."
                          : "Reinforce with practice quiz checkpoint."}
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
