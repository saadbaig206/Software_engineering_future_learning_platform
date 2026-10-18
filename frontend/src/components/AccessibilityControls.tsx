"use client";

import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Eye, Type, Zap, Volume2, Settings2, X } from "lucide-react";

export function AccessibilityControls() {
  const { a11y, updateA11y } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-controls="accessibility-drawer"
        aria-label="Open Accessibility & Display Preferences"
        className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 bg-white hover:bg-slate-50 hover:border-slate-300 transition text-xs font-medium shadow-sm"
      >
        <Settings2 className="w-4 h-4 text-indigo-600" aria-hidden="true" />
        <span>Accessibility</span>
      </button>

      {isOpen && (
        <div
          id="accessibility-drawer"
          role="region"
          aria-label="Accessibility Settings"
          className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 p-4 z-50 animate-in fade-in slide-in-from-top-2"
        >
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
              <Eye className="w-4 h-4 text-indigo-600" aria-hidden="true" />
              <span>WCAG 2.1 AA Settings</span>
            </h3>
            <button
              onClick={() => setIsOpen(false)}
              aria-label="Close accessibility panel"
              className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-4 pt-3 text-xs">
            {/* High Contrast Mode */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-slate-800">High Contrast Mode</p>
                <p className="text-slate-500 text-[11px]">7:1 ratio for low-vision clarity</p>
              </div>
              <button
                role="switch"
                aria-checked={a11y.contrastMode === "high"}
                onClick={() =>
                  updateA11y({
                    contrastMode: a11y.contrastMode === "high" ? "normal" : "high",
                  })
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  a11y.contrastMode === "high" ? "bg-indigo-600" : "bg-slate-300"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    a11y.contrastMode === "high" ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>

            {/* Font Size Scaling */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <p className="font-medium text-slate-800 flex items-center space-x-1">
                  <Type className="w-3.5 h-3.5 text-slate-500" />
                  <span>Text Scaling</span>
                </p>
                <span className="text-[11px] font-semibold uppercase text-indigo-600">
                  {a11y.fontSize}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-1.5">
                {(["normal", "large", "xlarge"] as const).map((size) => (
                  <button
                    key={size}
                    onClick={() => updateA11y({ fontSize: size })}
                    aria-pressed={a11y.fontSize === size}
                    className={`py-1.5 px-2 rounded-md font-medium text-center border transition ${
                      a11y.fontSize === size
                        ? "bg-indigo-50 border-indigo-600 text-indigo-700 font-bold"
                        : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    {size === "normal" ? "100%" : size === "large" ? "112%" : "125%"}
                  </button>
                ))}
              </div>
            </div>

            {/* Reduced Motion */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-slate-800 flex items-center space-x-1">
                  <Zap className="w-3.5 h-3.5 text-slate-500" />
                  <span>Reduce Motion</span>
                </p>
                <p className="text-slate-500 text-[11px]">Minimizes transitions & effects</p>
              </div>
              <button
                role="switch"
                aria-checked={a11y.reduceMotion}
                onClick={() => updateA11y({ reduceMotion: !a11y.reduceMotion })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  a11y.reduceMotion ? "bg-indigo-600" : "bg-slate-300"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    a11y.reduceMotion ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>

            {/* Closed Captions Default */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-slate-800 flex items-center space-x-1">
                  <Volume2 className="w-3.5 h-3.5 text-slate-500" />
                  <span>Captions by Default</span>
                </p>
                <p className="text-slate-500 text-[11px]">Auto-enable on video/audio</p>
              </div>
              <button
                role="switch"
                aria-checked={a11y.autoCaptions}
                onClick={() => updateA11y({ autoCaptions: !a11y.autoCaptions })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  a11y.autoCaptions ? "bg-indigo-600" : "bg-slate-300"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    a11y.autoCaptions ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
