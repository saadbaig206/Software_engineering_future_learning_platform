"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Course } from "../../lib/types";
import { getCourses } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import {
  Sparkles,
  PlusCircle,
  BookOpen,
  Edit,
  Eye,
  CheckCircle,
  Clock,
  Layers,
  ArrowRight,
} from "lucide-react";

export default function StudioOverviewPage() {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStudioCourses() {
      try {
        const data = await getCourses({ my_courses: true });
        setCourses(data);
      } catch (err) {
        console.error("Failed to load studio courses", err);
      } finally {
        setLoading(false);
      }
    }
    loadStudioCourses();
  }, []);

  const statusStyles = {
    DRAFT: "bg-amber-50 text-amber-700 border-amber-200",
    IN_REVIEW: "bg-blue-50 text-blue-700 border-blue-200",
    PUBLISHED: "bg-emerald-50 text-emerald-700 border-emerald-200",
    ARCHIVED: "bg-slate-100 text-slate-600 border-slate-200",
  };

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Studio Header */}
      <div className="card bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 rounded-2xl p-6 sm:p-10 text-white shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center space-x-2 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Content Designer Studio</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Curriculum Authoring & Publishing
          </h1>
          <p className="text-indigo-200 text-xs sm:text-sm max-w-xl">
            Design structured courses, assemble multi-type content blocks, upload media directly to S3,
            and preview before publishing.
          </p>
        </div>

        <Link
          href="/studio/courses/new"
          className="inline-flex items-center space-x-2 px-5 py-2.5 bg-indigo-500 hover:bg-indigo-600 text-white font-bold rounded-lg text-xs shadow-md transition shrink-0"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Create New Course</span>
        </Link>
      </div>

      {/* Author's Courses Table/Grid */}
      <section aria-labelledby="studio-courses-heading" className="space-y-4">
        <h2 id="studio-courses-heading" className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <BookOpen className="w-5 h-5 text-indigo-600" />
          <span>Your Authored Curricula</span>
        </h2>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 bg-slate-200 rounded-xl" />
            ))}
          </div>
        ) : courses.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200 p-8 space-y-4 shadow-xs">
            <BookOpen className="w-12 h-12 text-slate-300 mx-auto" />
            <h3 className="text-lg font-semibold text-slate-800">You haven't authored any courses yet</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              Start building a course curriculum with modules, lessons, video lectures, and simulation blocks.
            </p>
            <Link
              href="/studio/courses/new"
              className="inline-flex items-center space-x-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 shadow-sm transition"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Launch Course Creation Wizard</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
              <div
                key={course.id}
                className="card bg-white rounded-xl border border-slate-200 shadow-xs hover:border-indigo-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between overflow-hidden"
              >
                <div className="p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                        statusStyles[course.status] || "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {course.status}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      v{course.version}
                    </span>
                  </div>

                  <h3 className="font-bold text-base text-slate-900 line-clamp-2">
                    {course.title}
                  </h3>
                  <p className="text-slate-500 text-xs line-clamp-2 leading-relaxed">
                    {course.short_description || course.description}
                  </p>

                  <div className="flex items-center space-x-4 text-xs text-slate-400 pt-2 border-t border-slate-100">
                    <span className="flex items-center space-x-1">
                      <Layers className="w-3.5 h-3.5" />
                      <span>{course.module_count || 1} Modules</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{course.estimated_duration_minutes}m</span>
                    </span>
                  </div>
                </div>

                <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between gap-2">
                  <Link
                    href={`/courses/${course.slug}`}
                    className="inline-flex items-center space-x-1 px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg transition"
                    title="Preview as Learner"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Preview</span>
                  </Link>

                  <Link
                    href={`/studio/courses/${course.slug}`}
                    className="inline-flex items-center space-x-1 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-xs transition"
                  >
                    <Edit className="w-3.5 h-3.5" />
                    <span>Curriculum Studio</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
