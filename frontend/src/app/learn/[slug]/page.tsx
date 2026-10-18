"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Assessment,
  ContentBlock,
  Course,
  CourseProgressDetail,
  LearningPath,
  LearningPathItem,
  Lesson,
} from "../../../lib/types";
import {
  getAssessmentByLesson,
  getContentBlocks,
  getCourseProgress,
  getCourseSyllabus,
  getLearningPath,
  markLessonComplete,
  regenerateLearningPath,
  sendHeartbeat,
} from "../../../lib/api";
import { AssessmentPlayer } from "../../../components/AssessmentPlayer";
import { SimulationRunner } from "../../../components/SimulationRunner";
import { DiscussionPanel } from "../../../components/DiscussionPanel";
import { useAuth } from "../../../context/AuthContext";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  FileText,
  Download,
  Settings,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  Circle,
  Search,
  Sparkles,
  Zap,
  HelpCircle,
  Maximize,
  Sliders,
  ExternalLink,
  RotateCcw,
  Compass,
  AlertTriangle,
  Lightbulb,
} from "lucide-react";

export default function CoursePlayerPage() {
  const { slug } = useParams() as { slug: string };
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user, a11y } = useAuth();

  const [course, setCourse] = useState<Course | null>(null);
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
  const [blocks, setBlocks] = useState<ContentBlock[]>([]);
  const [progress, setProgress] = useState<CourseProgressDetail | null>(null);
  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);
  const [lessonAssessment, setLessonAssessment] = useState<Assessment | null>(null);
  const [showDiscussions, setShowDiscussions] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const [blocksLoading, setBlocksLoading] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenCooldown, setRegenCooldown] = useState(0);

  // Player controls state
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [audioOnlyMode, setAudioOnlyMode] = useState<boolean>(false);
  const [showTranscript, setShowTranscript] = useState<boolean>(true);
  const [transcriptSearch, setTranscriptSearch] = useState<string>("");
  const [videoQuality, setVideoQuality] = useState<string>("720p");
  const [completedLessons, setCompletedLessons] = useState<Record<string, boolean>>({});

  const videoRef = useRef<HTMLVideoElement>(null);
  const lastHeartbeatSentRef = useRef<number>(0);

  // Load course, progress, and adaptive path
  useEffect(() => {
    async function loadData() {
      try {
        const [courseData, progressData, pathData] = await Promise.all([
          getCourseSyllabus(slug),
          getCourseProgress(slug).catch(() => null),
          getLearningPath(slug).catch(() => null),
        ]);

        setCourse(courseData);
        setProgress(progressData);
        setLearningPath(pathData);

        // Populate completed map from backend
        if (progressData?.lessons) {
          const map: Record<string, boolean> = {};
          for (const p of progressData.lessons) {
            if (p.status === "COMPLETED") {
              map[p.lesson.id] = true;
            }
          }
          setCompletedLessons(map);
        }

        // Determine active lesson
        const requestedLessonId = searchParams.get("lesson");
        let targetLesson: Lesson | null = null;

        if (requestedLessonId && courseData.modules) {
          for (const m of courseData.modules) {
            const found = m.lessons?.find((l) => l.id === requestedLessonId);
            if (found) {
              targetLesson = found;
              break;
            }
          }
        }

        // Fallback to last active lesson from progress resume telemetry (FR-TRK-01 / FR-TRK-03)
        if (!targetLesson && progressData?.last_active_lesson) {
          for (const m of courseData.modules || []) {
            const found = m.lessons?.find(
              (l) => l.id === progressData.last_active_lesson?.lesson_id
            );
            if (found) {
              targetLesson = found;
              break;
            }
          }
        }

        if (!targetLesson && courseData.modules?.[0]?.lessons?.[0]) {
          targetLesson = courseData.modules[0].lessons[0];
        }

        setActiveLesson(targetLesson);
      } catch (err) {
        console.error("Failed to load player", err);
      } finally {
        setLoading(false);
      }
    }
    if (slug) loadData();
  }, [slug, searchParams]);

  // Load content blocks when active lesson changes
  useEffect(() => {
    async function loadLessonBlocks() {
      if (!activeLesson) return;
      setBlocksLoading(true);
      try {
        const blockList = await getContentBlocks(activeLesson.id);
        setBlocks(blockList);
      } catch (err) {
        console.error("Failed to load content blocks", err);
      } finally {
        setBlocksLoading(false);
      }

      try {
        const asm = await getAssessmentByLesson(activeLesson.id);
        setLessonAssessment(asm);
      } catch (err) {
        setLessonAssessment(null);
      }
    }
    loadLessonBlocks();
  }, [activeLesson]);

  // Heartbeat Telemetry Loop (FR-TRK-01)
  const emitHeartbeat = useCallback(
    async (isComplete = false) => {
      if (!activeLesson || !videoRef.current) return;
      const v = videoRef.current;
      const pos = Math.floor(v.currentTime);
      const dur = Math.floor(v.duration) || 1;
      const pct = isComplete ? 100 : Math.min(100, Math.floor((pos / dur) * 100));

      try {
        const res = await sendHeartbeat({
          lesson_id: activeLesson.id,
          position_seconds: pos,
          completion_percent: pct,
          is_completed: isComplete,
        });

        if (res.is_course_completed || isComplete) {
          setCompletedLessons((prev) => ({ ...prev, [activeLesson.id]: true }));
        }
      } catch (err) {
        console.warn("Heartbeat error", err);
      }
    },
    [activeLesson]
  );

  // Setup periodic heartbeat interval while video plays
  useEffect(() => {
    const interval = setInterval(() => {
      if (videoRef.current && !videoRef.current.paused && !videoRef.current.ended) {
        const now = Date.now();
        if (now - lastHeartbeatSentRef.current > 9000) {
          lastHeartbeatSentRef.current = now;
          emitHeartbeat(false);
        }
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [emitHeartbeat]);

  // Regenerate Adaptive Path handler (FR-PER-04)
  const handleRegeneratePath = async () => {
    if (regenCooldown > 0 || isRegenerating) return;
    setIsRegenerating(true);
    try {
      const updatedPath = await regenerateLearningPath(slug);
      setLearningPath(updatedPath);
      setRegenCooldown(60);
      const timer = setInterval(() => {
        setRegenCooldown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err: any) {
      if (err.response?.status === 429) {
        alert("Path regeneration is rate-limited to once per minute.");
      } else {
        console.error("Failed to regenerate path", err);
      }
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleManualComplete = async () => {
    if (!activeLesson) return;
    try {
      const res = await markLessonComplete(activeLesson.id);
      setCompletedLessons((prev) => ({ ...prev, [activeLesson.id]: true }));
      // Refresh learning path
      const p = await getLearningPath(slug).catch(() => null);
      if (p) setLearningPath(p);
    } catch (err) {
      console.error("Failed to mark lesson complete", err);
    }
  };

  const allLessons = course?.modules?.flatMap((m) => m.lessons || []) || [];
  const currentIdx = allLessons.findIndex((l) => l.id === activeLesson?.id);

  const handleNextLesson = () => {
    if (currentIdx !== -1 && currentIdx < allLessons.length - 1) {
      setActiveLesson(allLessons[currentIdx + 1]);
    }
  };

  const handlePrevLesson = () => {
    if (currentIdx > 0) {
      setActiveLesson(allLessons[currentIdx - 1]);
    }
  };

  // Find active learning path item recommendation for the current lesson
  const currentPathItem = learningPath?.items.find((i) => i.lesson.id === activeLesson?.id);
  const nextRecommendedItem = learningPath?.items.find((i) => !i.is_completed && i.lesson.id !== activeLesson?.id);

  if (loading) {
    return (
      <div className="flex h-screen bg-slate-900 text-white items-center justify-center">
        <div className="text-center space-y-3">
          <Sparkles className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
          <p className="text-sm font-medium">Initializing Learning Engine Player...</p>
        </div>
      </div>
    );
  }

  if (!course || !activeLesson) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-bold">Curriculum Not Available</h2>
        <Link href="/courses" className="mt-4 text-indigo-600 hover:underline">
          Return to Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-4rem)] overflow-hidden bg-slate-950 text-slate-100">
      {/* ========================================================= */}
      {/* Left Sidebar: Curriculum & Adaptive Sequence              */}
      {/* ========================================================= */}
      <aside
        aria-label="Course Modules Navigation"
        className="w-full lg:w-80 border-r border-slate-800 bg-slate-900/90 flex flex-col h-auto lg:h-full overflow-y-auto shrink-0"
      >
        <div className="p-4 border-b border-slate-800 bg-slate-900 sticky top-0 z-10 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-xs uppercase tracking-wider text-indigo-400">
              Curriculum Outline
            </h2>
            <p className="font-semibold text-sm text-slate-200 truncate max-w-[200px]">
              {course.title}
            </p>
          </div>
          <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
            {currentIdx + 1}/{allLessons.length}
          </span>
        </div>

        <nav className="p-3 space-y-4 flex-1">
          {course.modules?.map((module, mIdx) => (
            <div key={module.id} className="space-y-1">
              <div className="px-2 py-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                M{mIdx + 1}: {module.title}
              </div>
              <div className="space-y-0.5">
                {module.lessons?.map((lesson, lIdx) => {
                  const isActive = lesson.id === activeLesson.id;
                  const isDone = completedLessons[lesson.id];
                  const pathItem = learningPath?.items.find((i) => i.lesson.id === lesson.id);

                  return (
                    <button
                      key={lesson.id}
                      onClick={() => setActiveLesson(lesson)}
                      className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium text-left transition ${
                        isActive
                          ? "bg-indigo-600 text-white shadow-sm font-semibold"
                          : "text-slate-300 hover:bg-slate-800 hover:text-white"
                      }`}
                    >
                      <div className="flex items-center space-x-2 truncate">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleManualComplete();
                          }}
                          aria-label={`Mark ${lesson.title} as ${isDone ? "incomplete" : "complete"}`}
                          className="text-slate-400 hover:text-emerald-400 transition"
                        >
                          {isDone ? (
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <Circle className="w-4 h-4 text-slate-500" />
                          )}
                        </button>
                        <span className="truncate">
                          {lIdx + 1}. {lesson.title}
                        </span>
                      </div>

                      <div className="flex items-center space-x-1 shrink-0">
                        {pathItem?.path_type === "REMEDIATION" && (
                          <span className="text-[9px] font-bold bg-amber-500/20 text-amber-300 px-1 py-0.2 rounded border border-amber-500/30">
                            REMEDIAL
                          </span>
                        )}
                        {pathItem?.path_type === "ENRICHMENT" && (
                          <span className="text-[9px] font-bold bg-violet-500/20 text-violet-300 px-1 py-0.2 rounded border border-violet-500/30">
                            ADVANCED
                          </span>
                        )}
                        {lesson.is_preview && (
                          <span className="text-[9px] font-bold bg-emerald-500/20 text-emerald-300 px-1.5 py-0.2 rounded border border-emerald-500/30">
                            PREVIEW
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      {/* ========================================================= */}
      {/* Right / Main Viewport: Player & Adaptive Guidance         */}
      {/* ========================================================= */}
      <section
        aria-label="Lesson Content and Video Player"
        className="flex-1 flex flex-col h-full overflow-y-auto bg-slate-950"
      >
        {/* Adaptive Pedagogical Guidance Banner (FR-PER-03 / FR-PER-04) */}
        {currentPathItem && currentPathItem.path_type !== "STANDARD" && (
          <div
            className={`p-3 text-xs font-medium flex items-center justify-between border-b ${
              currentPathItem.path_type === "REMEDIATION"
                ? "bg-amber-950/70 border-amber-800 text-amber-200"
                : "bg-violet-950/70 border-violet-800 text-violet-200"
            }`}
          >
            <div className="flex items-center space-x-2">
              {currentPathItem.path_type === "REMEDIATION" ? (
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              ) : (
                <Lightbulb className="w-4 h-4 text-violet-400 shrink-0" />
              )}
              <span>{currentPathItem.reason}</span>
            </div>
            <button
              onClick={handleRegeneratePath}
              disabled={isRegenerating || regenCooldown > 0}
              className="px-2.5 py-1 bg-black/30 hover:bg-black/50 rounded text-[11px] font-bold flex items-center space-x-1 shrink-0 ml-4 transition disabled:opacity-50"
            >
              <RotateCcw className={`w-3 h-3 ${isRegenerating ? "animate-spin" : ""}`} />
              <span>
                {regenCooldown > 0 ? `Cooldown (${regenCooldown}s)` : "Refresh Path"}
              </span>
            </button>
          </div>
        )}

        {/* Top Lesson Header & Mode Toggles */}
        <div className="p-4 border-b border-slate-800 bg-slate-900/60 backdrop-blur-xs flex flex-wrap items-center justify-between gap-4 sticky top-0 z-20">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                Lesson {currentIdx + 1}
              </span>
              {activeLesson.is_preview && (
                <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                  Open Preview
                </span>
              )}
            </div>
            <h1 className="text-lg sm:text-xl font-bold text-white mt-1">
              {activeLesson.title}
            </h1>
          </div>

          {/* Quick Player Toolbar */}
          <div className="flex items-center space-x-2 text-xs">
            {/* Low-Bandwidth Audio-Only Mode Toggle (FR-MED-04) */}
            <button
              onClick={() => setAudioOnlyMode(!audioOnlyMode)}
              aria-pressed={audioOnlyMode}
              title="Toggle Low-Bandwidth Audio-Only mode (saves >80% bandwidth)"
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition ${
                audioOnlyMode
                  ? "bg-emerald-500/20 border-emerald-500 text-emerald-300"
                  : "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              <span>{audioOnlyMode ? "Audio-Only Mode (Active)" : "Low Bandwidth"}</span>
            </button>

            {/* Transcript Toggle */}
            <button
              onClick={() => setShowTranscript(!showTranscript)}
              aria-pressed={showTranscript}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition ${
                showTranscript
                  ? "bg-indigo-600 border-indigo-500 text-white"
                  : "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Transcript</span>
            </button>

            {/* Discussions Toggle */}
            <button
              onClick={() => setShowDiscussions(!showDiscussions)}
              aria-pressed={showDiscussions}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition ${
                showDiscussions
                  ? "bg-sky-600 border-sky-500 text-white"
                  : "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"
              }`}
            >
              <span>💬</span>
              <span>Discussions</span>
            </button>
          </div>
        </div>

        {/* Content Blocks Viewport */}
        <div className="p-4 sm:p-8 max-w-5xl mx-auto w-full space-y-8 flex-1">
          {blocksLoading ? (
            <div className="h-96 bg-slate-900 rounded-2xl animate-pulse flex items-center justify-center text-slate-500">
              Loading lesson media assets...
            </div>
          ) : blocks.length === 0 ? (
            <div className="space-y-6">
              {/* Responsive Video/Audio Container with Heartbeat Telemetry */}
              <div className="relative rounded-2xl overflow-hidden bg-black border border-slate-800 shadow-2xl aspect-video flex flex-col justify-between">
                {!audioOnlyMode ? (
                  <video
                    ref={videoRef}
                    controls
                    className="w-full h-full object-cover"
                    poster="/assets/lecture-poster.jpg"
                    playsInline
                    onEnded={() => emitHeartbeat(true)}
                  >
                    <source
                      src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
                      type="video/mp4"
                    />
                    <track
                      kind="captions"
                      src="/captions/sample-en.vtt"
                      srcLang="en"
                      label="English"
                      default={a11y.autoCaptions}
                    />
                    Your browser does not support HTML5 video streaming.
                  </video>
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex flex-col items-center justify-center p-8 text-center space-y-4">
                    <div className="w-20 h-20 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center animate-pulse">
                      <Volume2 className="w-10 h-10" />
                    </div>
                    <div className="space-y-1">
                      <h3 className="font-bold text-base text-white">Low-Bandwidth Mode Active</h3>
                      <p className="text-xs text-slate-400 max-w-md">
                        Video frames are suspended. Audio stream reduces data consumption by 85% for rural and mobile connections.
                      </p>
                    </div>
                    <audio controls className="w-full max-w-md">
                      <source
                        src="https://actions.google.com/sounds/v1/ambiences/rain_heavy.ogg"
                        type="audio/ogg"
                      />
                    </audio>
                  </div>
                )}
              </div>

              {/* Speed & Quality Selectors */}
              <div className="flex flex-wrap items-center justify-between gap-4 p-3 bg-slate-900 rounded-xl border border-slate-800 text-xs">
                <div className="flex items-center space-x-2">
                  <span className="text-slate-400 font-medium">Speed:</span>
                  {[0.75, 1, 1.25, 1.5, 2].map((s) => (
                    <button
                      key={s}
                      onClick={() => {
                        setPlaybackSpeed(s);
                        if (videoRef.current) videoRef.current.playbackRate = s;
                      }}
                      className={`px-2 py-1 rounded font-mono ${
                        playbackSpeed === s
                          ? "bg-indigo-600 text-white font-bold"
                          : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                      }`}
                    >
                      {s}x
                    </button>
                  ))}
                </div>

                <div className="flex items-center space-x-3 text-slate-400">
                  <span>Quality:</span>
                  <select
                    value={videoQuality}
                    onChange={(e) => setVideoQuality(e.target.value)}
                    className="bg-slate-800 text-slate-200 border border-slate-700 rounded px-2 py-1 text-xs"
                  >
                    <option value="1080p">1080p (HD)</option>
                    <option value="720p">720p (Default)</option>
                    <option value="360p">360p (Mobile)</option>
                  </select>
                </div>
              </div>
            </div>
          ) : (
            /* Render Dynamic Polymorphic Content Blocks */
            <div className="space-y-8">
              {blocks.map((block) => {
                if (block.block_type === "VIDEO") {
                  return (
                    <div
                      key={block.id}
                      className="rounded-2xl overflow-hidden bg-black border border-slate-800 shadow-xl aspect-video"
                    >
                      <video
                        ref={videoRef}
                        controls
                        className="w-full h-full object-cover"
                        playsInline
                        onEnded={() => emitHeartbeat(true)}
                      >
                        <source
                          src={
                            block.content_payload.url ||
                            block.content_payload.stream_url ||
                            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
                          }
                          type="video/mp4"
                        />
                        {block.content_payload.captions_url && (
                          <track
                            kind="captions"
                            src={block.content_payload.captions_url}
                            default={a11y.autoCaptions}
                          />
                        )}
                      </video>
                    </div>
                  );
                }

                if (block.block_type === "AUDIO") {
                  return (
                    <div
                      key={block.id}
                      className="p-6 bg-slate-900 rounded-xl border border-slate-800 space-y-3"
                    >
                      <div className="flex items-center space-x-2 text-indigo-400 font-semibold text-xs">
                        <Volume2 className="w-4 h-4" />
                        <span>{block.title || "Lecture Audio Recording"}</span>
                      </div>
                      <audio controls className="w-full">
                        <source
                          src={
                            block.content_payload.audio_url ||
                            block.content_payload.stream_url ||
                            "https://actions.google.com/sounds/v1/ambiences/rain_heavy.ogg"
                          }
                          type="audio/ogg"
                        />
                      </audio>
                    </div>
                  );
                }

                if (block.block_type === "TEXT") {
                  return (
                    <article
                      key={block.id}
                      className="prose prose-invert max-w-none bg-slate-900/40 p-6 rounded-2xl border border-slate-800 space-y-3"
                    >
                      {block.title && (
                        <h3 className="text-xl font-bold text-white">{block.title}</h3>
                      )}
                      <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap font-sans">
                        {block.content_payload.markdown ||
                          block.content_payload.html ||
                          "No textual content provided."}
                      </div>
                    </article>
                  );
                }

                if (block.block_type === "SIMULATION") {
                  return (
                    <SimulationRunner
                      key={block.id}
                      block={block}
                      onCompleted={() => emitHeartbeat(true)}
                    />
                  );
                }

                if (block.block_type === "PDF") {
                  return (
                    <div
                      key={block.id}
                      className="p-4 bg-slate-900 rounded-xl border border-slate-800 flex items-center justify-between"
                    >
                      <div className="flex items-center space-x-3">
                        <FileText className="w-6 h-6 text-indigo-400" />
                        <div>
                          <p className="font-semibold text-sm text-white">
                            {block.title || "Supplementary PDF"}
                          </p>
                          <p className="text-xs text-slate-400">Reference Lecture Notes</p>
                        </div>
                      </div>
                      <a
                        href={block.content_payload.download_url || "#"}
                        download
                        className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg flex items-center space-x-1 transition"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download</span>
                      </a>
                    </div>
                  );
                }

                return null;
              })}
            </div>
          )}

          {/* Synchronized Transcript Reader (FR-MED-03) */}
          {showTranscript && (
            <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  <h3 className="font-bold text-sm text-white">Interactive Closed Transcript</h3>
                </div>
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                  <input
                    type="text"
                    value={transcriptSearch}
                    onChange={(e) => setTranscriptSearch(e.target.value)}
                    placeholder="Search lecture words..."
                    className="w-full pl-8 pr-3 py-1 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="max-h-56 overflow-y-auto space-y-2 text-xs text-slate-300 leading-relaxed pr-2">
                <p>
                  <span className="font-mono text-indigo-400 font-semibold mr-2">[00:05]</span>
                  Welcome to Cloud-Native Microservices Architecture. Today we begin our journey into
                  distributed systems decomposition and domain boundary modeling.
                </p>
                <p>
                  <span className="font-mono text-indigo-400 font-semibold mr-2">[00:28]</span>
                  We will utilize bounded contexts from Domain-Driven Design (DDD) to isolate business invariants
                  and define clean asynchronous communication contracts.
                </p>
              </div>
            </div>
          )}

          {/* Formative / Summative Assessment Checkpoint (FR-ASM-01 - FR-ASM-06) */}
          {lessonAssessment && (
            <div className="mt-8">
              <AssessmentPlayer
                assessment={lessonAssessment}
                onCompleted={() => emitHeartbeat(true)}
              />
            </div>
          )}

          {/* Lesson Discussions Panel (FR-DIS-01 - FR-DIS-05) */}
          {showDiscussions && (
            <div className="mt-8">
              <DiscussionPanel
                courseSlug={slug}
                lessonId={activeLesson.id}
                isInstructor={user?.role === "INSTRUCTOR" || user?.role === "ADMIN"}
              />
            </div>
          )}

          {/* Lesson Navigation & Completion Footer */}
          <div className="pt-6 border-t border-slate-800 flex items-center justify-between">
            <button
              onClick={handlePrevLesson}
              disabled={currentIdx === 0}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Previous Lesson</span>
            </button>

            <button
              onClick={handleManualComplete}
              className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl border text-xs font-semibold transition ${
                completedLessons[activeLesson.id]
                  ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                  : "bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20"
              }`}
            >
              <CheckCircle className="w-4 h-4" />
              <span>
                {completedLessons[activeLesson.id] ? "Completed ✓" : "Mark as Complete"}
              </span>
            </button>

            <button
              onClick={handleNextLesson}
              disabled={currentIdx === allLessons.length - 1}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm transition"
            >
              <span>Next Lesson</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
