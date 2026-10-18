import React from "react";
import Link from "next/link";
import {
  CheckCircle2,
  Zap,
  Shield,
  Cpu,
  ArrowRight,
  BookOpen,
  Sparkles,
  Eye,
  Sliders,
  GraduationCap,
} from "lucide-react";

export default function HomePage() {
  return (
    <div className="space-y-16 py-12">
      {/* Hero Section */}
      <section className="max-w-5xl mx-auto px-4 text-center space-y-6">
        <div className="inline-flex items-center space-x-2 bg-indigo-50 border border-indigo-100 px-3 py-1 rounded-full text-xs font-semibold text-indigo-700">
          <Sparkles className="w-3.5 h-3.5" />
          <span>PHASE 5: LEARNER EXPERIENCE & CONTENT DESIGNER STUDIO</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
          Adaptive learning that empowers <br className="hidden sm:inline" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">
            every student and educator.
          </span>
        </h1>

        <p className="max-w-2xl mx-auto text-base sm:text-lg text-slate-600 leading-relaxed">
          A scalable, accessible (WCAG 2.1 AA), and modular online education platform.
          Featuring multi-format video lectures, low-bandwidth audio fallback, sandboxed simulations,
          and direct-to-S3 curriculum authoring.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Link
            href="/courses"
            className="inline-flex items-center space-x-2 px-6 py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 shadow-md transition text-sm"
          >
            <BookOpen className="w-4 h-4" />
            <span>Explore Course Catalog</span>
            <ArrowRight className="w-4 h-4" />
          </Link>

          <Link
            href="/studio"
            className="inline-flex items-center space-x-2 px-6 py-3 bg-white text-indigo-700 font-bold rounded-xl border border-indigo-200 hover:bg-indigo-50 transition shadow-sm text-sm"
          >
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span>Content Designer Studio</span>
          </Link>
        </div>
      </section>

      {/* Feature Pillar Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="card bg-white p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-4 hover:border-indigo-300 transition">
            <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center font-bold">
              01
            </div>
            <h2 className="text-xl font-bold text-slate-900">Multi-Format Player</h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              HTML5 streaming video with WebVTT closed captions, synchronized interactive transcript search,
              playback speed controls, and low-bandwidth audio-only mode saving &gt;80% bandwidth.
            </p>
          </div>

          <div className="card bg-white p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-4 hover:border-indigo-300 transition">
            <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center font-bold">
              02
            </div>
            <h2 className="text-xl font-bold text-slate-900">Content Designer Studio</h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              Block-based curriculum editor with direct presigned S3 uploads, live student preview,
              and strict publishing invariants that guarantee complete courses before release.
            </p>
          </div>

          <div className="card bg-white p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-4 hover:border-indigo-300 transition">
            <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center font-bold">
              03
            </div>
            <h2 className="text-xl font-bold text-slate-900">WCAG 2.1 AA Accessibility</h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              Full keyboard focus management, high-contrast display mode (&gt;7:1 contrast ratio),
              rem-based font scaling (100% to 125%), and screen reader friendly ARIA landmarks.
            </p>
          </div>
        </div>
      </section>

      {/* Subsystem Pipeline Card */}
      <section className="max-w-5xl mx-auto px-4">
        <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-3xl p-8 sm:p-10 shadow-xl space-y-6">
          <div className="flex items-center space-x-3">
            <Cpu className="w-6 h-6 text-indigo-400" />
            <span className="text-xs tracking-wider uppercase text-indigo-300 font-semibold">
              Live Verified Architecture Stack
            </span>
          </div>

          <h3 className="text-xl sm:text-2xl font-bold">
            Next.js 15 App Router &rarr; Django 5 REST API &rarr; Neon PostgreSQL &rarr; Redis Cache &rarr; Celery Workers
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-xs">
              <p className="text-xs text-indigo-200">Database</p>
              <p className="font-bold text-sm text-white">Neon PostgreSQL</p>
            </div>
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-xs">
              <p className="text-xs text-indigo-200">Cache / Broker</p>
              <p className="font-bold text-sm text-white">Redis 7 In-Memory</p>
            </div>
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-xs">
              <p className="text-xs text-indigo-200">Task Fleet</p>
              <p className="font-bold text-sm text-white">Celery 5 Workers</p>
            </div>
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-xs">
              <p className="text-xs text-indigo-200">Media Pipeline</p>
              <p className="font-bold text-sm text-white">Direct Presigned S3</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
