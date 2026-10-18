"use client";

import React, { useState, useEffect, useRef } from "react";
import { ContentBlock } from "../lib/types";
import { reportSimulationScore } from "../lib/api";

interface SimulationRunnerProps {
  block: ContentBlock;
  onCompleted?: () => void;
}

export function SimulationRunner({ block, onCompleted }: SimulationRunnerProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [latestScore, setLatestScore] = useState<number | null>(null);
  const [isPassed, setIsPassed] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const payload = block.content_payload || {};
  const embedUrl = payload.embed_url || "/simulations/circuit-breaker.html";
  const passingScore = payload.passing_score || 70;

  useEffect(() => {
    const handleMessage = async (event: MessageEvent) => {
      if (!event.data || typeof event.data !== "object") return;

      const { type, payload: simData } = event.data;

      // Handle Handshake from Simulation Frame
      if (type === "SIM_READY") {
        if (iframeRef.current && iframeRef.current.contentWindow) {
          iframeRef.current.contentWindow.postMessage(
            {
              type: "SIM_INIT",
              payload: {
                theme: "dark",
                high_contrast: false,
                passing_score: passingScore,
              },
            },
            "*"
          );
        }
      }

      // Handle Score Telemetry Report
      if (type === "SIM_SCORE_REPORT" && simData) {
        const score = typeof simData.score_percent === "number" ? simData.score_percent : 0;
        setLatestScore(score);

        if (score >= passingScore) {
          setIsPassed(true);
        }

        try {
          const res = await reportSimulationScore({
            block_id: block.id,
            score_percent: score,
            completed: simData.completed || score >= passingScore,
            telemetry: simData.telemetry || {},
          });

          if (res.passed || res.lesson_completed) {
            setStatusMessage(`🎉 Simulation Checkpoint Passed! (${score}% achieved)`);
            if (onCompleted) onCompleted();
          }
        } catch (err) {
          console.error("Failed to report simulation score to backend:", err);
        }
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [block.id, passingScore, onCompleted]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Simulation Header */}
      <div className="p-4 bg-slate-850 border-b border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Interactive Simulation Checkpoint
          </span>
          <h3 className="text-base font-bold text-slate-100 mt-1">{block.title}</h3>
        </div>
        <div className="flex items-center gap-3">
          {latestScore !== null && (
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold ${
                isPassed
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-slate-800 text-slate-300 border border-slate-700"
              }`}
            >
              Current Score: {latestScore}%
            </span>
          )}
          <span className="text-xs text-slate-400">Target: {passingScore}%</span>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 bg-emerald-500/10 border-b border-emerald-500/20 text-emerald-300 text-xs font-semibold flex items-center justify-between">
          <span>{statusMessage}</span>
          <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-2xs">
            COMPLETED
          </span>
        </div>
      )}

      {/* Sandboxed Simulation Frame (FR-SIM-01) */}
      <div className="w-full relative" style={{ height: "540px" }}>
        <iframe
          ref={iframeRef}
          src={embedUrl}
          title={block.title}
          sandbox="allow-scripts allow-same-origin"
          className="w-full h-full border-none bg-slate-950"
        />
      </div>
    </div>
  );
}
