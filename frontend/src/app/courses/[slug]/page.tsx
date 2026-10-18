"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Course } from "../../../lib/types";
import { getCourseSyllabus, enrollInCourse } from "../../../lib/api";
import { useAuth } from "../../../context/AuthContext";
import {
  Clock,
  Layers,
  CheckCircle,
  Lock,
  PlayCircle,
  ArrowRight,
  User as UserIcon,
  BookOpen,
  Sparkles,
  ShieldCheck,
} from "lucide-react";

export default function CourseDetailPage() {
  const { slug } = useParams() as { slug: string };
  const router = useRouter();
  const { user } = useAuth();
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadSyllabus() {
      try {
        const data = await getCourseSyllabus(slug);
        setCourse(data);
      } catch (err) {
        console.error("Failed to load course syllabus", err);
      } finally {
        setLoading(false);
      }
    }
    if (slug) loadSyllabus();
  }, [slug]);

  const handleEnroll = async () => {
    if (!user) {
      router.push(`/login?redirect=/courses/${slug}`);
      return;
    }
    setEnrolling(true);
    try {
      await enrollInCourse(slug);
      setMessage("You are successfully enrolled!");
      // Update local enrolled state
      setCourse((prev) => (prev ? { ...prev, is_enrolled: true } : null));
    } catch (err: any) {
      setMessage(err.response?.data?.detail || "Enrollment failed. Please try again.");
    } finally {
      setEnrolling(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-16 px-4 animate-pulse space-y-6">
        <div className="h-48 bg-slate-200 rounded-2xl" />
        <div className="h-64 bg-slate-200 rounded-2xl" />
      </div>
    );
  }

  if (!course) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-bold text-slate-800">Course Not Found</h2>
        <Link href="/courses" className="mt-4 inline-block text-indigo-600 hover:underline">
          Return to Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      {/* Course Hero Header */}
      <section aria-labelledby="course-title" className="card bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-6 sm:p-10 space-y-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200">
            {course.difficulty}
          </span>
          {course.category && (
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
              {course.category.name}
            </span>
          )}
          <span className="px-3 py-1 rounded-full text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 flex items-center space-x-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Academic Peer Reviewed</span>
          </span>
        </div>

        <div className="space-y-3">
          <h1 id="course-title" className="text-2xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            {course.title}
          </h1>
          <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
            {course.description}
          </p>
        </div>

        {/* Metadata & Instructor Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-slate-100 text-xs text-slate-500">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-500 to-violet-500 text-white font-bold flex items-center justify-center text-sm shadow-xs">
              {course.instructor.name[0]}
            </div>
            <div>
              <p className="font-semibold text-slate-800 text-sm">{course.instructor.name}</p>
              <p className="text-slate-400">Curriculum Lead · {course.instructor.email}</p>
            </div>
          </div>

          <div className="flex items-center space-x-6 text-slate-600">
            <span className="flex items-center space-x-1.5 font-medium">
              <Clock className="w-4 h-4 text-indigo-600" />
              <span>{course.estimated_duration_minutes} Minutes Total</span>
            </span>
            <span className="flex items-center space-x-1.5 font-medium">
              <Layers className="w-4 h-4 text-indigo-600" />
              <span>{course.modules?.length || 0} Modules</span>
            </span>
          </div>
        </div>

        {/* Enrollment Banner / CTA */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div>
            <p className="text-xs font-semibold text-slate-800">
              {course.is_enrolled ? "You are enrolled in this curriculum" : "Free Academic Enrollment"}
            </p>
            <p className="text-[11px] text-slate-500">
              Access all lecture videos, transcripts, interactive simulations, and skill mastery tracking.
            </p>
            {message && <p className="text-xs font-medium text-emerald-600 mt-1">{message}</p>}
          </div>

          {course.is_enrolled ? (
            <Link
              href={`/learn/${course.slug}`}
              className="w-full sm:w-auto px-6 py-2.5 bg-emerald-600 text-white text-xs font-bold rounded-lg hover:bg-emerald-700 shadow-sm transition flex items-center justify-center space-x-1.5"
            >
              <span>Continue in Player</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <button
              onClick={handleEnroll}
              disabled={enrolling}
              className="w-full sm:w-auto px-6 py-2.5 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700 shadow-sm transition flex items-center justify-center space-x-1.5 disabled:opacity-50"
            >
              <span>{enrolling ? "Enrolling..." : "Enroll in Course"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </section>

      {/* Curriculum & Syllabus Accordion */}
      <section aria-labelledby="syllabus-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="syllabus-heading" className="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <BookOpen className="w-5 h-5 text-indigo-600" />
            <span>Course Syllabus & Learning Outline</span>
          </h2>
          <span className="text-xs text-slate-500">
            {course.modules?.reduce((acc, m) => acc + (m.lessons?.length || 0), 0)} Lessons Total
          </span>
        </div>

        <div className="space-y-4">
          {course.modules?.map((module, mIdx) => (
            <div key={module.id} className="card bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="bg-slate-50/70 p-4 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600">
                    Module {mIdx + 1}
                  </span>
                  <h3 className="font-bold text-sm text-slate-800">{module.title}</h3>
                </div>
                <span className="text-xs text-slate-500">
                  {module.lessons?.length || 0} Lessons
                </span>
              </div>

              <div className="divide-y divide-slate-100">
                {module.lessons?.map((lesson, lIdx) => {
                  const canAccess = course.is_enrolled || lesson.is_preview;
                  return (
                    <div
                      key={lesson.id}
                      className="p-4 flex items-center justify-between hover:bg-slate-50/50 transition text-xs"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="text-slate-400 font-mono text-[11px]">
                          {mIdx + 1}.{lIdx + 1}
                        </div>
                        <div>
                          <p className="font-medium text-slate-800 flex items-center space-x-2">
                            <span>{lesson.title}</span>
                            {lesson.is_preview && (
                              <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold px-2 py-0.2 rounded-full text-[10px]">
                                Free Preview
                              </span>
                            )}
                          </p>
                          <span className="text-slate-400 text-[11px]">
                            {lesson.estimated_duration_minutes} mins · {lesson.is_required ? "Required" : "Optional"}
                          </span>
                        </div>
                      </div>

                      <div>
                        {canAccess ? (
                          <Link
                            href={`/learn/${course.slug}?lesson=${lesson.id}`}
                            className="inline-flex items-center space-x-1 font-semibold text-indigo-600 hover:text-indigo-700 bg-indigo-50 px-3 py-1.5 rounded-md hover:bg-indigo-100 transition"
                          >
                            <PlayCircle className="w-3.5 h-3.5" />
                            <span>{lesson.is_preview && !course.is_enrolled ? "Watch Preview" : "Start"}</span>
                          </Link>
                        ) : (
                          <span
                            className="inline-flex items-center space-x-1 text-slate-400 bg-slate-100 px-3 py-1.5 rounded-md font-medium"
                            title="Enroll to unlock this lesson"
                          >
                            <Lock className="w-3.5 h-3.5" />
                            <span>Locked</span>
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
