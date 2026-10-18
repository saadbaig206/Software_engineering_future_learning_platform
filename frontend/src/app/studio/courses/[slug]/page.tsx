"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Course, Module, Lesson } from "../../../../lib/types";
import {
  getCourseBySlug,
  createModule,
  createLesson,
  updateLesson,
  publishCourse,
  archiveCourse,
} from "../../../../lib/api";
import {
  Sparkles,
  Layers,
  PlusCircle,
  Edit3,
  CheckCircle,
  AlertCircle,
  Eye,
  Send,
  Lock,
  ArrowLeft,
  BookOpen,
  Check,
  X,
  Clock,
} from "lucide-react";

export default function CourseCurriculumStudioPage() {
  const { slug } = useParams() as { slug: string };
  const router = useRouter();

  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [newModuleTitle, setNewModuleTitle] = useState("");
  const [addingModule, setAddingModule] = useState(false);
  const [addingLessonForModuleId, setAddingLessonForModuleId] = useState<string | null>(null);
  const [newLessonTitle, setNewLessonTitle] = useState("");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadData = async () => {
    try {
      const data = await getCourseBySlug(slug);
      setCourse(data);
    } catch (err) {
      console.error("Failed to load course", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (slug) loadData();
  }, [slug]);

  const handleAddModule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newModuleTitle.trim() || !course) return;
    try {
      await createModule({
        course: course.id,
        title: newModuleTitle,
        position: (course.modules?.length || 0) + 1,
      });
      setNewModuleTitle("");
      setAddingModule(false);
      await loadData();
    } catch (err) {
      console.error("Failed to add module", err);
    }
  };

  const handleAddLesson = async (moduleId: string) => {
    if (!newLessonTitle.trim()) return;
    try {
      const targetMod = course?.modules?.find((m) => m.id === moduleId);
      await createLesson({
        module: moduleId,
        title: newLessonTitle,
        position: (targetMod?.lessons?.length || 0) + 1,
        is_published: true, // default published
      });
      setNewLessonTitle("");
      setAddingLessonForModuleId(null);
      await loadData();
    } catch (err) {
      console.error("Failed to add lesson", err);
    }
  };

  const handleTogglePreview = async (lesson: Lesson) => {
    try {
      await updateLesson(lesson.id, { is_preview: !lesson.is_preview });
      await loadData();
    } catch (err) {
      console.error("Failed to toggle preview", err);
    }
  };

  const handleTogglePublishLesson = async (lesson: Lesson) => {
    try {
      await updateLesson(lesson.id, { is_published: !lesson.is_published });
      await loadData();
    } catch (err) {
      console.error("Failed to toggle lesson publish state", err);
    }
  };

  const handlePublishCourse = async () => {
    setPublishing(true);
    setFeedback(null);
    try {
      const res = await publishCourse(slug);
      setFeedback({ type: "success", text: res.message });
      await loadData();
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Course publication validation failed.";
      setFeedback({ type: "error", text: Array.isArray(msg) ? msg.join(" ") : String(msg) });
    } finally {
      setPublishing(false);
    }
  };

  if (loading) {
    return <div className="max-w-5xl mx-auto py-16 px-4 animate-pulse">Loading curriculum editor...</div>;
  }

  if (!course) {
    return <div className="text-center py-20 font-bold">Course not found.</div>;
  }

  // Publishing invariant checks (FR-CRS-06, D-015)
  const hasModules = (course.modules?.length || 0) > 0;
  const allModulesHavePublishedLessons =
    hasModules &&
    course.modules!.every((m) => m.lessons && m.lessons.some((l) => l.is_published));
  const canPublish = hasModules && allModulesHavePublishedLessons;

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      {/* Top back navigation & status */}
      <div className="flex items-center justify-between">
        <Link
          href="/studio"
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Studio Overview</span>
        </Link>

        <div className="flex items-center space-x-2">
          <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {course.status}
          </span>
          <Link
            href={`/courses/${course.slug}`}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center space-x-1 px-3 py-1 rounded-lg border border-indigo-200 bg-indigo-50"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Preview As Student</span>
          </Link>
        </div>
      </div>

      {feedback && (
        <div
          role="alert"
          className={`p-4 rounded-xl flex items-center space-x-2 text-xs font-semibold ${
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
              : "bg-rose-50 text-rose-800 border border-rose-200"
          }`}
        >
          {feedback.type === "success" ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
          <span>{feedback.text}</span>
        </div>
      )}

      {/* Course Title Banner */}
      <div className="card bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">
            Curriculum Builder
          </span>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            {course.title}
          </h1>
          <p className="text-slate-500 text-xs mt-1">
            {course.difficulty} · {course.estimated_duration_minutes} Minutes
          </p>
        </div>

        {/* Publishing Invariant Action Card */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-col items-end space-y-2 shrink-0">
          <button
            onClick={handlePublishCourse}
            disabled={publishing || course.status === "PUBLISHED"}
            className={`px-5 py-2.5 rounded-lg text-xs font-bold shadow-sm transition flex items-center space-x-1.5 ${
              course.status === "PUBLISHED"
                ? "bg-emerald-600 text-white cursor-default"
                : canPublish
                ? "bg-indigo-600 hover:bg-indigo-700 text-white"
                : "bg-slate-300 text-slate-500 cursor-not-allowed"
            }`}
          >
            <Send className="w-3.5 h-3.5" />
            <span>
              {course.status === "PUBLISHED"
                ? "Published to Catalog"
                : publishing
                ? "Validating & Publishing..."
                : "Publish Course"}
            </span>
          </button>
          <p className="text-[10px] text-slate-400">
            {course.status === "PUBLISHED"
              ? "Active on public catalog"
              : canPublish
              ? "All publishing criteria satisfied"
              : "Requires at least 1 module with published lessons"}
          </p>
        </div>
      </div>

      {/* Publishing Invariant Checklist Drawer */}
      <div className="p-4 bg-indigo-50/50 rounded-xl border border-indigo-100 text-xs space-y-2">
        <p className="font-semibold text-slate-800 text-[11px] uppercase tracking-wider flex items-center space-x-1.5">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Course Release Checklist (FR-CRS-06)</span>
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-600">
          <div className="flex items-center space-x-2">
            {hasModules ? <Check className="w-4 h-4 text-emerald-600" /> : <X className="w-4 h-4 text-rose-500" />}
            <span>At least 1 module defined ({course.modules?.length || 0})</span>
          </div>
          <div className="flex items-center space-x-2">
            {allModulesHavePublishedLessons ? (
              <Check className="w-4 h-4 text-emerald-600" />
            ) : (
              <X className="w-4 h-4 text-rose-500" />
            )}
            <span>Every module contains at least 1 published lesson</span>
          </div>
        </div>
      </div>

      {/* Curriculum Hierarchy Structure */}
      <section aria-labelledby="modules-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="modules-heading" className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <Layers className="w-5 h-5 text-indigo-600" />
            <span>Modules & Pedagogical Lessons</span>
          </h2>

          <button
            onClick={() => setAddingModule(true)}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-lg text-xs font-semibold transition"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Module</span>
          </button>
        </div>

        {/* Add Module Inline Form */}
        {addingModule && (
          <form onSubmit={handleAddModule} className="p-4 bg-white rounded-xl border border-indigo-200 shadow-sm space-y-3">
            <h3 className="font-bold text-xs text-slate-800">Add New Curriculum Module</h3>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                required
                value={newModuleTitle}
                onChange={(e) => setNewModuleTitle(e.target.value)}
                placeholder="e.g. Module 1: Foundations of Distributed Algorithms"
                className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold transition"
              >
                Save Module
              </button>
              <button
                type="button"
                onClick={() => setAddingModule(false)}
                className="px-3 py-2 bg-slate-100 text-slate-600 rounded-lg text-xs font-semibold"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Modules List */}
        <div className="space-y-4">
          {course.modules?.map((module, mIdx) => (
            <div key={module.id} className="card bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="bg-slate-50/80 p-4 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">
                    Module {mIdx + 1}
                  </span>
                  <h3 className="font-bold text-sm text-slate-900">{module.title}</h3>
                </div>

                <button
                  onClick={() => setAddingLessonForModuleId(module.id)}
                  className="inline-flex items-center space-x-1 px-2.5 py-1 bg-white border border-slate-200 hover:border-indigo-300 text-slate-700 text-xs font-medium rounded-md shadow-xs transition"
                >
                  <PlusCircle className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Add Lesson</span>
                </button>
              </div>

              {/* Add Lesson Inline Form */}
              {addingLessonForModuleId === module.id && (
                <div className="p-3 bg-indigo-50/40 border-b border-slate-200 flex items-center space-x-2">
                  <input
                    type="text"
                    required
                    value={newLessonTitle}
                    onChange={(e) => setNewLessonTitle(e.target.value)}
                    placeholder="Lesson title (e.g. Lesson 1.2: Leader Election)"
                    className="flex-1 px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <button
                    type="button"
                    onClick={() => handleAddLesson(module.id)}
                    className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold"
                  >
                    Add
                  </button>
                  <button
                    type="button"
                    onClick={() => setAddingLessonForModuleId(null)}
                    className="px-2 py-1.5 text-slate-500 text-xs font-semibold"
                  >
                    Cancel
                  </button>
                </div>
              )}

              {/* Lessons List */}
              <div className="divide-y divide-slate-100">
                {module.lessons?.map((lesson, lIdx) => (
                  <div
                    key={lesson.id}
                    className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/50 transition text-xs"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-slate-400 font-mono text-[11px]">
                        {mIdx + 1}.{lIdx + 1}
                      </span>
                      <div>
                        <p className="font-semibold text-slate-900">{lesson.title}</p>
                        <p className="text-slate-400 text-[11px]">
                          {lesson.estimated_duration_minutes} mins · {lesson.is_required ? "Required" : "Optional"}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {/* Free Preview Toggle (FR-CRS-02) */}
                      <button
                        type="button"
                        onClick={() => handleTogglePreview(lesson)}
                        className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition border ${
                          lesson.is_preview
                            ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                            : "bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100"
                        }`}
                        title="Allow unauthenticated guests and non-enrolled students to preview"
                      >
                        {lesson.is_preview ? "Free Preview ON" : "Preview OFF"}
                      </button>

                      {/* Publish / Draft Toggle */}
                      <button
                        type="button"
                        onClick={() => handleTogglePublishLesson(lesson)}
                        className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition border ${
                          lesson.is_published
                            ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                            : "bg-amber-50 text-amber-700 border-amber-200"
                        }`}
                      >
                        {lesson.is_published ? "Published" : "Draft"}
                      </button>

                      {/* Content Blocks Editor link */}
                      <Link
                        href={`/studio/courses/${course.slug}/lessons/${lesson.id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-md shadow-xs transition"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Edit Blocks</span>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
