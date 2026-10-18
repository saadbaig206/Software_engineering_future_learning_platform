"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Course, Category } from "../../lib/types";
import { getCourses, getCategories } from "../../lib/api";
import {
  Search,
  Filter,
  Clock,
  BookOpen,
  Sparkles,
  ArrowRight,
  GraduationCap,
  Layers,
} from "lucide-react";

export default function CourseCatalogPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("ALL");

  useEffect(() => {
    async function loadCatalog() {
      setLoading(true);
      try {
        const [courseData, catData] = await Promise.all([
          getCourses({
            search: search || undefined,
            category: selectedCategory !== "all" ? selectedCategory : undefined,
            difficulty: selectedDifficulty !== "ALL" ? selectedDifficulty : undefined,
          }),
          getCategories(),
        ]);
        setCourses(courseData);
        setCategories(catData);
      } catch (err) {
        console.error("Failed to load catalog", err);
      } finally {
        setLoading(false);
      }
    }
    const timer = setTimeout(loadCatalog, 300);
    return () => clearTimeout(timer);
  }, [search, selectedCategory, selectedDifficulty]);

  const difficultyColors = {
    BEGINNER: "bg-emerald-50 text-emerald-700 border-emerald-200",
    INTERMEDIATE: "bg-amber-50 text-amber-700 border-amber-200",
    ADVANCED: "bg-rose-50 text-rose-700 border-rose-200",
    ALL_LEVELS: "bg-indigo-50 text-indigo-700 border-indigo-200",
  };

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Header & Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 p-8 sm:p-12 text-white shadow-xl">
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold backdrop-blur-md border border-indigo-400/30">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Accessible · Modular · Personalized</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Explore Open Pedagogical Curricula
          </h1>
          <p className="text-indigo-200 text-sm sm:text-base leading-relaxed">
            Discover peer-reviewed university courses designed with multi-format media,
            free preview checkpoints, and accessible learning pathways.
          </p>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <section aria-label="Course Filters" className="bg-white p-4 sm:p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          {/* Search Input */}
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search courses by keyword, topic, or instructor..."
              aria-label="Search courses"
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
            />
          </div>

          {/* Difficulty Dropdown */}
          <div className="flex items-center space-x-3 w-full md:w-auto">
            <label htmlFor="difficulty-select" className="text-xs font-medium text-slate-600 whitespace-nowrap">
              Difficulty:
            </label>
            <select
              id="difficulty-select"
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="py-2 px-3 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="ALL">All Difficulties</option>
              <option value="BEGINNER">Beginner</option>
              <option value="INTERMEDIATE">Intermediate</option>
              <option value="ADVANCED">Advanced</option>
              <option value="ALL_LEVELS">All Levels</option>
            </select>
          </div>
        </div>

        {/* Categories Pills */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
          <button
            onClick={() => setSelectedCategory("all")}
            aria-pressed={selectedCategory === "all"}
            className={`px-3 py-1.5 rounded-full font-medium whitespace-nowrap transition ${
              selectedCategory === "all"
                ? "bg-indigo-600 text-white font-semibold"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            All Categories
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.slug)}
              aria-pressed={selectedCategory === cat.slug}
              className={`px-3 py-1.5 rounded-full font-medium whitespace-nowrap transition ${
                selectedCategory === cat.slug
                  ? "bg-indigo-600 text-white font-semibold"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {cat.name} {cat.course_count ? `(${cat.course_count})` : ""}
            </button>
          ))}
        </div>
      </section>

      {/* Courses Grid */}
      <section aria-label="Course Listings">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-72 bg-slate-200 rounded-xl" />
            ))}
          </div>
        ) : courses.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200 p-8 space-y-4">
            <GraduationCap className="w-12 h-12 text-slate-300 mx-auto" />
            <h3 className="text-lg font-semibold text-slate-800">No courses match your criteria</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              Try adjusting your search keyword or clearing category filters to explore available curricula.
            </p>
            <button
              onClick={() => {
                setSearch("");
                setSelectedCategory("all");
                setSelectedDifficulty("ALL");
              }}
              className="px-4 py-2 text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
              <article
                key={course.id}
                className="group card bg-white rounded-xl border border-slate-200/80 hover:border-indigo-300 hover:shadow-lg transition-all duration-200 flex flex-col justify-between overflow-hidden"
              >
                <div>
                  {/* Card Thumbnail / Header */}
                  <div className="h-40 bg-gradient-to-tr from-slate-800 to-indigo-900 p-5 flex flex-col justify-between text-white relative">
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${
                          difficultyColors[course.difficulty] || "bg-indigo-50 text-indigo-700"
                        }`}
                      >
                        {course.difficulty}
                      </span>
                      {course.category && (
                        <span className="text-[11px] font-medium bg-black/40 backdrop-blur-xs px-2 py-0.5 rounded">
                          {course.category.name}
                        </span>
                      )}
                    </div>
                    <h2 className="font-bold text-lg leading-snug group-hover:text-indigo-300 transition line-clamp-2">
                      {course.title}
                    </h2>
                  </div>

                  {/* Body Content */}
                  <div className="p-5 space-y-3">
                    <p className="text-slate-600 text-xs line-clamp-2 leading-relaxed">
                      {course.short_description || course.description}
                    </p>

                    {/* Metadata strip */}
                    <div className="flex items-center space-x-4 text-xs text-slate-500 pt-2 border-t border-slate-100">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{course.estimated_duration_minutes} mins</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <Layers className="w-3.5 h-3.5 text-slate-400" />
                        <span>{course.module_count || 1} Modules</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Footer & CTA */}
                <div className="p-5 pt-0 flex items-center justify-between border-t border-slate-100 bg-slate-50/50 py-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold text-[10px] flex items-center justify-center">
                      {course.instructor.name[0]}
                    </div>
                    <span className="text-xs text-slate-700 font-medium truncate max-w-[120px]">
                      {course.instructor.name}
                    </span>
                  </div>

                  <Link
                    href={`/courses/${course.slug}`}
                    className="inline-flex items-center space-x-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700 group/btn"
                    aria-label={`View syllabus and details for ${course.title}`}
                  >
                    <span>View Syllabus</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
