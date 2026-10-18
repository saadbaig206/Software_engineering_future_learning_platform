"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ContentBlock, ContentBlockType } from "../../../../../../lib/types";
import {
  getContentBlocks,
  createContentBlock,
  deleteContentBlock,
  getPresignedUploadUrl,
  confirmMediaUpload,
  uploadFileDirectToStorage,
} from "../../../../../../lib/api";
import {
  ArrowLeft,
  PlusCircle,
  FileText,
  Video,
  Sparkles,
  Download,
  Trash2,
  UploadCloud,
  CheckCircle,
  AlertCircle,
  Save,
} from "lucide-react";

export default function LessonBlockEditorPage() {
  const { slug, lessonId } = useParams() as { slug: string; lessonId: string };

  const [blocks, setBlocks] = useState<ContentBlock[]>([]);
  const [loading, setLoading] = useState(true);

  // New Block State
  const [blockType, setBlockType] = useState<ContentBlockType>("TEXT");
  const [title, setTitle] = useState("");
  const [textContent, setTextContent] = useState("");
  const [simUrl, setSimUrl] = useState("https://simulations.futurelearning.test/circuits");
  const [pdfDownloadUrl, setPdfDownloadUrl] = useState("");

  // Direct S3 Upload State (FR-MED-01)
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const loadBlocks = async () => {
    try {
      const data = await getContentBlocks(lessonId);
      setBlocks(data);
    } catch (err) {
      console.error("Failed to load blocks", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (lessonId) loadBlocks();
  }, [lessonId]);

  const handleCreateTextBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createContentBlock({
        lesson: lessonId,
        block_type: "TEXT",
        title: title || "Lecture Notes",
        position: blocks.length + 1,
        content_payload: { markdown: textContent },
      });
      setTitle("");
      setTextContent("");
      await loadBlocks();
    } catch (err) {
      console.error("Failed to create text block", err);
    }
  };

  const handleCreateSimulationBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createContentBlock({
        lesson: lessonId,
        block_type: "SIMULATION",
        title: title || "Interactive Simulation Checkpoint",
        position: blocks.length + 1,
        content_payload: {
          sim_url: simUrl,
          sandbox_flags: "allow-scripts allow-same-origin",
        },
      });
      setTitle("");
      await loadBlocks();
    } catch (err) {
      console.error("Failed to create simulation block", err);
    }
  };

  const handleDirectS3Upload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus("Requesting presigned upload ticket from Django API...");

    try {
      // 1. Phase A: Request signed ticket (FR-MED-01, D-016)
      const ticket = await getPresignedUploadUrl(lessonId, {
        filename: selectedFile.name,
        mime_type: selectedFile.type || "video/mp4",
        size_bytes: selectedFile.size,
      });

      // 2. Phase B: Direct Browser-to-Storage PUT with telemetry
      setUploadStatus("Streaming binary directly to S3 bucket (bypassing web workers)...");
      await uploadFileDirectToStorage(ticket, selectedFile, (pct) => {
        setUploadProgress(pct);
      });

      // 3. Phase C: Confirmation Handshake & Celery Task (FR-MED-02)
      setUploadStatus("Upload complete. Queuing asynchronous validation & thumbnail pipeline...");
      const confirmRes = await confirmMediaUpload({
        storage_key: ticket.storage_key,
        original_filename: selectedFile.name,
        mime_type: selectedFile.type || "video/mp4",
        size_bytes: selectedFile.size,
      });

      // 4. Create content block referencing the new asset
      await createContentBlock({
        lesson: lessonId,
        block_type: selectedFile.type.startsWith("audio/") ? "AUDIO" : "VIDEO",
        title: title || selectedFile.name,
        position: blocks.length + 1,
        media_asset: confirmRes.media_asset_id,
        content_payload: {
          storage_key: ticket.storage_key,
          original_filename: selectedFile.name,
        },
      });

      setSelectedFile(null);
      setUploadProgress(null);
      setUploadStatus("Media successfully attached to lesson!");
      setTitle("");
      await loadBlocks();
    } catch (err: any) {
      setUploadStatus(err.response?.data?.detail || "Upload pipeline failed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteBlock = async (id: string) => {
    try {
      await deleteContentBlock(id);
      await loadBlocks();
    } catch (err) {
      console.error("Failed to delete block", err);
    }
  };

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-8">
      <Link
        href={`/studio/courses/${slug}`}
        className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Return to Curriculum Hierarchy</span>
      </Link>

      <div className="space-y-1">
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Lesson Content Block Studio
        </h1>
        <p className="text-xs text-slate-500">
          Assemble polymorphic media blocks: Rich text, direct S3 streaming video, simulations, and documents
        </p>
      </div>

      {/* Existing Blocks List */}
      <section aria-labelledby="existing-blocks" className="space-y-4">
        <h2 id="existing-blocks" className="text-base font-bold text-slate-900">
          Existing Blocks in this Lesson ({blocks.length})
        </h2>

        {loading ? (
          <div className="h-40 bg-slate-200 rounded-xl animate-pulse" />
        ) : blocks.length === 0 ? (
          <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-500">
            No content blocks added yet. Use the authoring drawer below to add rich text, upload video, or embed an interactive simulation.
          </div>
        ) : (
          <div className="space-y-3">
            {blocks.map((block) => (
              <div
                key={block.id}
                className="card bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between text-xs"
              >
                <div className="flex items-center space-x-3">
                  <span className="font-bold uppercase tracking-wider text-[10px] px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                    {block.block_type}
                  </span>
                  <div>
                    <p className="font-semibold text-slate-900">{block.title || "Untitled Block"}</p>
                    <p className="text-slate-400 text-[11px]">Position: {block.position}</p>
                  </div>
                </div>

                <button
                  onClick={() => handleDeleteBlock(block.id)}
                  className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md transition"
                  title="Delete Block"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Add Content Block Form */}
      <section aria-labelledby="add-block-heading" className="card bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6">
        <h2 id="add-block-heading" className="text-base font-bold text-slate-900 flex items-center space-x-2">
          <PlusCircle className="w-5 h-5 text-indigo-600" />
          <span>Add New Content Block</span>
        </h2>

        {/* Block Type Selector Tabs */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <button
            type="button"
            onClick={() => setBlockType("TEXT")}
            className={`py-2 px-3 rounded-lg font-semibold flex items-center justify-center space-x-1.5 border transition ${
              blockType === "TEXT"
                ? "bg-indigo-50 border-indigo-600 text-indigo-700"
                : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Rich Text / Markdown</span>
          </button>

          <button
            type="button"
            onClick={() => setBlockType("VIDEO")}
            className={`py-2 px-3 rounded-lg font-semibold flex items-center justify-center space-x-1.5 border transition ${
              blockType === "VIDEO"
                ? "bg-indigo-50 border-indigo-600 text-indigo-700"
                : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Video className="w-4 h-4" />
            <span>Direct S3 Video Upload</span>
          </button>

          <button
            type="button"
            onClick={() => setBlockType("SIMULATION")}
            className={`py-2 px-3 rounded-lg font-semibold flex items-center justify-center space-x-1.5 border transition ${
              blockType === "SIMULATION"
                ? "bg-indigo-50 border-indigo-600 text-indigo-700"
                : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Interactive Simulation</span>
          </button>
        </div>

        {/* Form Body for TEXT */}
        {blockType === "TEXT" && (
          <form onSubmit={handleCreateTextBlock} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Block Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Theoretical Framework"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Markdown Body</label>
              <textarea
                rows={6}
                required
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                placeholder="### Heading&#10;Write detailed lecture concepts here with code snippets..."
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800 font-mono"
              />
            </div>
            <button
              type="submit"
              className="px-5 py-2 bg-indigo-600 text-white font-bold rounded-lg shadow-sm hover:bg-indigo-700 transition"
            >
              Attach Text Block
            </button>
          </form>
        )}

        {/* Form Body for DIRECT S3 VIDEO / MEDIA UPLOAD (FR-MED-01) */}
        {blockType === "VIDEO" && (
          <div className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Video Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Lecture 1: Raft Consensus Proof"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800"
              />
            </div>

            <div className="p-6 border-2 border-dashed border-slate-300 rounded-xl text-center space-y-2 bg-slate-50">
              <UploadCloud className="w-8 h-8 text-indigo-600 mx-auto" />
              <p className="font-semibold text-slate-800">
                Direct Browser-to-S3 Upload (FR-MED-01)
              </p>
              <p className="text-[11px] text-slate-500">
                Zero Django worker load. Files up to 1 GB upload directly with real-time progress.
              </p>
              <input
                type="file"
                accept="video/*,audio/*"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="text-xs text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
            </div>

            {uploadProgress !== null && (
              <div className="space-y-1">
                <div className="flex justify-between font-semibold text-slate-700">
                  <span>Uploading to Object Storage...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all duration-200"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {uploadStatus && (
              <p className="text-[11px] font-medium text-indigo-600">{uploadStatus}</p>
            )}

            <button
              type="button"
              onClick={handleDirectS3Upload}
              disabled={!selectedFile || isUploading}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg shadow-sm transition disabled:opacity-50"
            >
              {isUploading ? "Uploading Directly..." : "Start Direct S3 Upload"}
            </button>
          </div>
        )}

        {/* Form Body for SIMULATION (FR-SIM-01) */}
        {blockType === "SIMULATION" && (
          <form onSubmit={handleCreateSimulationBlock} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Simulation Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Interactive Logic Gate Sandbox"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Sandboxed Frame URL</label>
              <input
                type="url"
                required
                value={simUrl}
                onChange={(e) => setSimUrl(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800 font-mono"
              />
            </div>
            <button
              type="submit"
              className="px-5 py-2 bg-indigo-600 text-white font-bold rounded-lg shadow-sm hover:bg-indigo-700 transition"
            >
              Attach Simulation Block
            </button>
          </form>
        )}
      </section>
    </div>
  );
}
