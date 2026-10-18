"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { CourseProgressDetail, Enrollment, Skill } from "../../lib/types";
import {
  getMyEnrollments,
  getCourseProgress,
  getStudentSkills,
  resetCourseProgress,
} from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import {
  BookOpen,
  CheckCircle,
  Clock,
  ArrowRight,
  Sparkles,
  Flame,
  Award,
  GraduationCap,
  RotateCcw,
  Compass,
  Check,
  TrendingUp,
} from "lucide-react";

export default function LearnerDashboardPage() {
  const { user } = useAuth();
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [progressMap, setProgressMap] = useState<Record<string, CourseProgressDetail>>({});
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [resettingSlug, setResettingSlug] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [enrData, skillsData] = await Promise.all([
          getMyEnrollments(),
          getStudentSkills().catch(() => []),
        ]);
        setEnrollments(enrData);
        setSkills(skillsData);

        // Fetch detailed progress for each enrollment
        const progressEntries = await Promise.all(
          enrData.map(async (enr) => {
            try {
              const p = await getCourseProgress(enr.course.slug);
              return [enr.course.slug, p] as const;
            } catch {
              return null;
            }
          })
        );
        const pMap: Record<string, CourseProgressDetail> = {};
        for (const entry of progressEntries) {
          if (entry) pMap[entry[0]] = entry[1];
        }
        setProgressMap(pMap);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  const handleResetProgress = async (courseSlug: string) => {
    if (!window.confirm("Are you sure you want to reset your progress for this course? Your past completed units will be marked uncompleted so you can re-study.")) {
      return;
    }
    setResettingSlug(courseSlug);
    try {
      await resetCourseProgress(courseSlug);
      const updated = await getCourseProgress(courseSlug);
      setProgressMap((prev) => ({ ...prev, [courseSlug]: updated }));
    } catch (err) {
      console.error("Failed to reset progress", err);
      alert("Failed to reset progress. Please try again.");
    } finally {
      setResettingSlug(null);
    }
  };

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-10">
      {/* Welcome & Learning Telemetry Banner */}
      <div className="card bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 rounded-2xl p-6 sm:p-10 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2 max-w-xl">
          <div className="inline-flex items-center space-x-2 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Learner Portal · Personalized Learning</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome back, {user?.first_name || "Learner"}
          </h1>
          <p className="text-indigo-200 text-xs sm:text-sm">
            Continuous progress tracking with resume checkpoints and Knowledge-Space adaptive recommendations.
          </p>
        </div>

        {/* Telemetry Stats Strip */}
        <div className="flex items-center space-x-4 bg-black/20 p-4 rounded-xl border border-white/10 backdrop-blur-md">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-300">Active Streak</p>
              <p className="font-extrabold text-sm text-white">4 Days</p>
            </div>
          </div>

          <div className="h-8 w-px bg-white/20" />

          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-300">Enrolled</p>
              <p className="font-extrabold text-sm text-white">{enrollments.length} Courses</p>
            </div>
          </div>
        </div>
      </div>

      {/* Enrolled Courses Section with Granular Progress */}
      <section aria-labelledby="enrolled-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="enrolled-heading" className="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <BookOpen className="w-5 h-5 text-indigo-600" />
            <span>My Enrolled Curricula</span>
          </h2>
          <Link
            href="/courses"
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center space-x-1"
          >
            <span>Browse Catalog</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-60 bg-slate-200 rounded-xl" />
            ))}
          </div>
        ) : enrollments.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200 p-8 space-y-4 shadow-xs">
            <GraduationCap className="w-12 h-12 text-slate-300 mx-auto" />
            <h3 className="text-lg font-semibold text-slate-800">No active course enrollments yet</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              Explore the public catalog to enroll in university curricula and begin your personalized learning journey.
            </p>
            <Link
              href="/courses"
              className="inline-flex items-center space-x-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 shadow-sm transition"
            >
              <span>Explore Course Catalog</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {enrollments.map((enr) => {
              const progress = progressMap[enr.course.slug];
              const percent = progress ? progress.completion_percent : 0;
              const isDone = progress?.is_completed || enr.status === "COMPLETED";
              const lastActive = progress?.last_active_lesson;

              return (
                <div
                  key={enr.id}
                  className="card bg-white rounded-xl border border-slate-200 shadow-xs hover:border-indigo-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between overflow-hidden"
                >
                  <div className="p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                          isDone
                            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                            : "bg-indigo-50 text-indigo-700 border-indigo-200"
                        }`}
                      >
                        {isDone ? "Completed" : "In Progress"}
                      </span>
                      <span className="text-xs text-slate-400">
                        {progress ? `${progress.completed_lessons}/${progress.total_required_lessons} Lessons` : "0 Lessons"}
                      </span>
                    </div>

                    <h3 className="font-bold text-base text-slate-900 line-clamp-2">
                      {enr.course.title}
                    </h3>

                    {/* Progress Bar (FR-TRK-02 / FR-TRK-03) */}
                    <div className="space-y-1.5 pt-2">
                      <div className="flex justify-between text-xs font-medium text-slate-600">
                        <span>Course Completion</span>
                        <span className="font-bold text-indigo-600">{percent}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                        <div
                          className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500"
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>

                    {lastActive && (
                      <p className="text-xs text-slate-500 truncate">
                        Last Active: <span className="font-medium text-slate-700">{lastActive.title}</span>
                      </p>
                    )}
                  </div>

                  <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                    {/* Re-study / Reset Progress (FR-TRK-04) */}
                    {isDone ? (
                      <button
                        onClick={() => handleResetProgress(enr.course.slug)}
                        disabled={resettingSlug === enr.course.slug}
                        className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-indigo-600 font-medium transition"
                        title="Reset progress to re-study course"
                      >
                        <RotateCcw className={`w-3.5 h-3.5 ${resettingSlug === enr.course.slug ? "animate-spin" : ""}`} />
                        <span>Re-study</span>
                      </button>
                    ) : (
                      <div className="text-xs text-slate-400">
                        {enr.course.difficulty}
                      </div>
                    )}

                    {/* Direct Resume Button seeking to last active lesson */}
                    <Link
                      href={
                        lastActive
                          ? `/learn/${enr.course.slug}?lesson=${lastActive.lesson_id}`
                          : `/learn/${enr.course.slug}`
                      }
                      className="inline-flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-xs transition"
                    >
                      <span>{isDone ? "Review Course" : "Resume Learning"}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Pedagogical Competencies & Skill Mastery (FR-PER-01 / FR-PER-02) */}
      <section aria-labelledby="skills-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="skills-heading" className="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-indigo-600" />
            <span>Pedagogical Skill Mastery & Competencies</span>
          </h2>
          <span className="text-xs text-slate-400">Knowledge-Space Theory DAG</span>
        </div>

        {skills.length === 0 ? (
          <div className="p-6 bg-white rounded-xl border border-slate-200 text-center text-sm text-slate-500">
            No pedagogical skills assessed yet. Complete interactive quizzes and lesson units to build your competency graph.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {skills.map((skill) => {
              const mastery = skill.mastery_score ?? 0;
              const isMastered = mastery >= 85;
              const isRemediating = mastery < 70;

              return (
                <div
                  key={skill.id}
                  className="bg-white rounded-xl border border-slate-200 p-5 space-y-3 shadow-xs hover:border-slate-300 transition"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-sm text-slate-900">{skill.name}</h4>
                      <p className="text-xs text-slate-500 line-clamp-1">{skill.description}</p>
                    </div>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        isMastered
                          ? "bg-violet-50 text-violet-700 border border-violet-200"
                          : isRemediating
                          ? "bg-amber-50 text-amber-700 border border-amber-200"
                          : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      }`}
                    >
                      {isMastered ? "Mastered" : isRemediating ? "Remediation" : "Competent"}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold text-slate-700">
                      <span>Mastery Score</span>
                      <span className="font-bold text-indigo-600">{mastery}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full transition-all duration-500 ${
                          isMastered
                            ? "bg-violet-600"
                            : isRemediating
                            ? "bg-amber-500"
                            : "bg-emerald-500"
                        }`}
                        style={{ width: `${mastery}%` }}
                      />
                    </div>
                  </div>

                  {skill.prerequisites?.length > 0 && (
                    <div className="pt-1 text-[11px] text-slate-400">
                      Prerequisites: {skill.prerequisites.map((p) => p.name).join(", ")}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
