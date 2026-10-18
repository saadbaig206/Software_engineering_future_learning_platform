"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Category } from "../../../../lib/types";
import { createCourse, getCategories } from "../../../../lib/api";
import {
  Sparkles,
  BookOpen,
  ArrowRight,
  ArrowLeft,
  Clock,
  Layers,
  Save,
} from "lucide-react";

export default function NewCoursePage() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [title, setTitle] = useState("");
  const [categoryId, setCategoryId] = useState<string>("");
  const [difficulty, setDifficulty] = useState("BEGINNER");
  const [duration, setDuration] = useState<number>(60);
  const [shortDesc, setShortDesc] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCategories().then((cats) => {
      setCategories(cats);
      if (cats.length > 0) setCategoryId(cats[0].id);
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const course = await createCourse({
        title,
        category: categoryId || null,
        difficulty,
        estimated_duration_minutes: Number(duration),
        short_description: shortDesc,
        description,
      });
      router.push(`/studio/courses/${course.slug}`);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.title?.[0] ||
          "Failed to initialize course. Please check required fields."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto space-y-6">
      <Link
        href="/studio"
        className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Return to Studio</span>
      </Link>

      <div className="space-y-1">
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Author a New Curriculum
        </h1>
        <p className="text-xs text-slate-500">
          Define core metadata, pedagogical difficulty, and syllabus overview
        </p>
      </div>

      {error && (
        <div role="alert" className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs font-medium text-rose-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="card bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs space-y-5 text-xs">
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Course Title *</label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Distributed Consensus & Raft Architecture"
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800 font-medium"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Academic Category</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800"
            >
              <option value="">No Category</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Pedagogical Difficulty</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800"
            >
              <option value="BEGINNER">Beginner</option>
              <option value="INTERMEDIATE">Intermediate</option>
              <option value="ADVANCED">Advanced</option>
              <option value="ALL_LEVELS">All Levels</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Est. Duration (Minutes)</label>
            <input
              type="number"
              min={10}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800"
            />
          </div>
        </div>

        <div>
          <label className="block font-semibold text-slate-700 mb-1">Short Description (Catalog Summary)</label>
          <input
            type="text"
            value={shortDesc}
            onChange={(e) => setShortDesc(e.target.value)}
            placeholder="A one-sentence summary for card previews..."
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800"
          />
        </div>

        <div>
          <label className="block font-semibold text-slate-700 mb-1">Full Course Syllabus Overview *</label>
          <textarea
            rows={5}
            required
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Comprehensive description of topics, prerequisites, and learning outcomes..."
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800 font-sans"
          />
        </div>

        <div className="pt-4 border-t border-slate-100 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg shadow-sm transition flex items-center space-x-2 disabled:opacity-50 text-xs"
          >
            <Save className="w-4 h-4" />
            <span>{loading ? "Initializing..." : "Create Course & Open Curriculum Builder"}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
