"use client";

import React, { useState, useEffect } from "react";
import { getSmokeTest, SmokeTestResponse } from "@/lib/api";
import { CheckCircle2, AlertTriangle, RefreshCw, Server, Database, Layers, Activity } from "lucide-react";

export default function SmokeTestPage() {
  const [data, setData] = useState<SmokeTestResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSmokeTest = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getSmokeTest();
      setData(result);
    } catch (err: any) {
      setError(err?.message || "Failed to communicate with FutureLearning backend API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSmokeTest();
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            End-to-End Pipeline Smoke Test
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Validating real-time communication: Next.js &rarr; Django DRF &rarr; Neon PostgreSQL &rarr; Redis &rarr; Celery.
          </p>
        </div>

        <button
          onClick={fetchSmokeTest}
          disabled={loading}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition shadow-sm text-sm font-medium self-start sm:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          <span>Re-run Smoke Test</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-start space-x-3 text-red-800">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-sm">Cross-System Request Failed</p>
            <p className="text-xs mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {loading && !data && (
        <div className="p-12 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-indigo-600" />
          <p className="text-sm font-medium">Executing cross-system smoke test across all tiers...</p>
        </div>
      )}

      {data && (
        <div className="space-y-6">
          {/* Status Banner */}
          <div
            className={`p-6 rounded-2xl border flex items-center justify-between ${
              data.all_passed
                ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                : "bg-amber-50 border-amber-200 text-amber-900"
            }`}
          >
            <div className="flex items-center space-x-3">
              {data.all_passed ? (
                <CheckCircle2 className="w-8 h-8 text-emerald-600" />
              ) : (
                <AlertTriangle className="w-8 h-8 text-amber-600" />
              )}
              <div>
                <h2 className="text-lg font-bold">
                  {data.all_passed
                    ? "Full Pipeline Operational: All 4 Subsystems Passed"
                    : "Pipeline Active with Warnings"}
                </h2>
                <p className="text-xs opacity-80 mt-0.5">
                  Verified at {new Date(data.timestamp * 1000).toLocaleTimeString()} · Total Latency:{" "}
                  {data.total_elapsed_ms} ms
                </p>
              </div>
            </div>
            <span className="text-xs font-mono bg-white/60 px-3 py-1 rounded-full font-bold">
              {data.all_passed ? "STATUS: 200 OK" : "STATUS: MULTI-STATUS"}
            </span>
          </div>

          {/* Subsystem Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Step 1: Django */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-slate-900 font-semibold text-sm">
                  <Server className="w-4 h-4 text-indigo-600" />
                  <span>1. Django API Gateway</span>
                </div>
                <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                  {data.pipeline["1_django_api"]?.status}
                </span>
              </div>
              <p className="text-xs text-slate-600">{data.pipeline["1_django_api"]?.message}</p>
            </div>

            {/* Step 2: Neon PostgreSQL */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-slate-900 font-semibold text-sm">
                  <Database className="w-4 h-4 text-indigo-600" />
                  <span>2. Neon PostgreSQL Database</span>
                </div>
                <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                  {data.pipeline["2_neon_postgres"]?.status}
                </span>
              </div>
              <p className="text-xs text-slate-600">
                Connected to <strong className="font-semibold text-slate-800">{data.pipeline["2_neon_postgres"]?.database_name}</strong> (
                {data.pipeline["2_neon_postgres"]?.engine_version}) via secure SSL pooling.
              </p>
            </div>

            {/* Step 3: Redis Cache */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-slate-900 font-semibold text-sm">
                  <Layers className="w-4 h-4 text-indigo-600" />
                  <span>3. Redis Cache & Broker</span>
                </div>
                <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                  {data.pipeline["3_redis_cache"]?.status}
                </span>
              </div>
              <p className="text-xs text-slate-600">
                Cache key <code className="bg-slate-100 px-1 py-0.5 rounded text-indigo-700">{data.pipeline["3_redis_cache"]?.key_tested}</code> verified read/write integrity.
              </p>
            </div>

            {/* Step 4: Celery */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-slate-900 font-semibold text-sm">
                  <Activity className="w-4 h-4 text-indigo-600" />
                  <span>4. Celery Async Task Worker</span>
                </div>
                <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                  {data.pipeline["4_celery_task"]?.status}
                </span>
              </div>
              <p className="text-xs text-slate-600">
                Dispatched task <code className="bg-slate-100 px-1 py-0.5 rounded text-indigo-700">{data.pipeline["4_celery_task"]?.task_id || "debug_smoke_task"}</code> with asynchronous state tracking.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
