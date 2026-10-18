"use client";

import React, { useState, useEffect } from "react";
import { DiscussionThread, DiscussionPost } from "../lib/types";
import {
  getCourseThreads,
  createThread,
  getThreadDetail,
  addThreadReply,
  toggleThreadVote,
  togglePostVote,
  endorsePost,
  fileContentReport,
} from "../lib/api";

interface DiscussionPanelProps {
  courseSlug: string;
  lessonId?: string;
  isInstructor?: boolean;
}

export function DiscussionPanel({ courseSlug, lessonId, isInstructor }: DiscussionPanelProps) {
  const [threads, setThreads] = useState<DiscussionThread[]>([]);
  const [activeThread, setActiveThread] = useState<DiscussionThread | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Modals state
  const [isNewThreadOpen, setIsNewThreadOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newBody, setNewBody] = useState("");
  const [replyBody, setReplyBody] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Report modal state
  const [reportingTarget, setReportingTarget] = useState<{ threadId?: string; postId?: string } | null>(null);
  const [reportReason, setReportReason] = useState("SPAM");
  const [reportDetails, setReportDetails] = useState("");
  const [reportSuccess, setReportSuccess] = useState(false);

  const fetchThreads = async () => {
    try {
      setIsLoading(true);
      const data = await getCourseThreads(courseSlug, {
        lesson_id: lessonId,
        search: searchQuery || undefined,
      });
      setThreads(data);
    } catch (err) {
      console.error("Error loading discussion threads:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchThreads();
  }, [courseSlug, lessonId, searchQuery]);

  const handleSelectThread = async (threadId: string) => {
    try {
      const full = await getThreadDetail(threadId);
      setActiveThread(full);
    } catch (err) {
      console.error("Error loading thread detail:", err);
    }
  };

  const handleCreateThread = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newBody.trim() || isSubmitting) return;

    try {
      setIsSubmitting(true);
      const created = await createThread(courseSlug, {
        title: newTitle,
        body: newBody,
        lesson_id: lessonId,
      });
      setThreads([created, ...threads]);
      setActiveThread(created);
      setIsNewThreadOpen(false);
      setNewTitle("");
      setNewBody("");
    } catch (err) {
      console.error("Error creating discussion thread:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddReply = async (e: React.FormEvent, parentId?: string) => {
    e.preventDefault();
    if (!activeThread || !replyBody.trim() || isSubmitting) return;

    try {
      setIsSubmitting(true);
      const post = await addThreadReply(activeThread.id, {
        body: replyBody,
        parent_id: parentId,
      });

      // Refresh thread
      handleSelectThread(activeThread.id);
      setReplyBody("");
    } catch (err) {
      console.error("Error adding reply:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleThreadVote = async (threadId: string) => {
    try {
      const res = await toggleThreadVote(threadId);
      setThreads(
        threads.map((t) =>
          t.id === threadId ? { ...t, upvotes_count: res.upvotes_count, has_upvoted: res.has_upvoted } : t
        )
      );
      if (activeThread && activeThread.id === threadId) {
        setActiveThread({ ...activeThread, upvotes_count: res.upvotes_count, has_upvoted: res.has_upvoted });
      }
    } catch (err) {
      console.error("Error toggling thread vote:", err);
    }
  };

  const handleTogglePostVote = async (postId: string) => {
    try {
      const res = await togglePostVote(postId);
      if (activeThread) {
        handleSelectThread(activeThread.id);
      }
    } catch (err) {
      console.error("Error toggling post vote:", err);
    }
  };

  const handleEndorsePost = async (postId: string) => {
    try {
      await endorsePost(postId);
      if (activeThread) {
        handleSelectThread(activeThread.id);
      }
    } catch (err) {
      console.error("Error endorsing post:", err);
    }
  };

  const handleFileReport = async () => {
    if (!reportingTarget) return;
    try {
      await fileContentReport({
        thread_id: reportingTarget.threadId,
        post_id: reportingTarget.postId,
        reason: reportReason,
        details: reportDetails,
      });
      setReportSuccess(true);
      setTimeout(() => {
        setReportingTarget(null);
        setReportSuccess(false);
        setReportDetails("");
      }, 1500);
    } catch (err) {
      console.error("Error filing content report:", err);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl flex flex-col text-slate-100 min-h-[500px]">
      {/* Header */}
      <div className="p-4 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {activeThread && (
            <button
              onClick={() => setActiveThread(null)}
              className="mr-1 p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white"
            >
              ← Back
            </button>
          )}
          <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
            💬 Course & Lesson Discussions
            {lessonId && (
              <span className="text-2xs font-semibold px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                Lesson Context
              </span>
            )}
          </h3>
        </div>

        {!activeThread && (
          <button
            onClick={() => setIsNewThreadOpen(true)}
            className="px-3 py-1.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs rounded-lg transition shadow-md shadow-sky-500/15"
          >
            + Ask Question
          </button>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-4 overflow-y-auto">
        {!activeThread ? (
          // Threads List View
          <div className="space-y-3">
            {/* Search Input */}
            <div className="mb-4">
              <input
                type="text"
                placeholder="Search discussions or keywords..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700/60 rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>

            {isLoading ? (
              <div className="py-12 text-center text-xs text-slate-400">Loading discussions...</div>
            ) : threads.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-400">
                No discussion threads yet. Be the first to ask a question!
              </div>
            ) : (
              threads.map((thread) => (
                <div
                  key={thread.id}
                  onClick={() => handleSelectThread(thread.id)}
                  className="p-3.5 rounded-lg bg-slate-800/40 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 cursor-pointer transition flex items-start justify-between gap-3"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2">
                      {thread.is_pinned && (
                        <span className="text-2xs font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          📌 PINNED
                        </span>
                      )}
                      <h4 className="font-semibold text-sm text-slate-100 hover:text-sky-400 transition">
                        {thread.title}
                      </h4>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-2">{thread.body}</p>
                    <div className="flex items-center gap-3 text-2xs text-slate-500 pt-1">
                      <span>By {thread.author?.full_name || thread.author?.email || "Student"}</span>
                      <span>·</span>
                      <span>{new Date(thread.created_at).toLocaleDateString()}</span>
                      <span>·</span>
                      <span>💬 {thread.replies_count || 0} replies</span>
                    </div>
                  </div>

                  {/* Upvote Pill */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleThreadVote(thread.id);
                    }}
                    className={`flex flex-col items-center justify-center min-w-[36px] py-1 px-1.5 rounded border text-xs font-semibold ${
                      thread.has_upvoted
                        ? "bg-sky-500/20 text-sky-400 border-sky-500/40"
                        : "bg-slate-800/80 text-slate-400 border-slate-700/60 hover:text-white"
                    }`}
                  >
                    <span>▲</span>
                    <span>{thread.upvotes_count}</span>
                  </button>
                </div>
              ))
            )}
          </div>
        ) : (
          // Active Thread Conversation View
          <div className="space-y-6">
            {/* Thread Original Post */}
            <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {activeThread.is_pinned && (
                      <span className="text-2xs font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300">
                        PINNED
                      </span>
                    )}
                    <h3 className="font-bold text-base text-slate-100">{activeThread.title}</h3>
                  </div>
                  <div className="text-xs text-slate-400">
                    Posted by <strong className="text-slate-300">{activeThread.author?.full_name || activeThread.author?.email}</strong> on {new Date(activeThread.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggleThreadVote(activeThread.id)}
                    className={`px-3 py-1 rounded text-xs font-bold border flex items-center gap-1 ${
                      activeThread.has_upvoted
                        ? "bg-sky-500/20 text-sky-300 border-sky-500/40"
                        : "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
                    }`}
                  >
                    ▲ {activeThread.upvotes_count}
                  </button>
                  <button
                    onClick={() => setReportingTarget({ threadId: activeThread.id })}
                    className="text-xs text-slate-500 hover:text-rose-400"
                    title="Report Thread"
                  >
                    🚩
                  </button>
                </div>
              </div>

              <div className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed pt-2 border-t border-slate-700/40">
                {activeThread.body}
              </div>
            </div>

            {/* Replies List */}
            <div className="space-y-4 pl-2">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Replies ({activeThread.posts?.length || 0})
              </h4>

              {(!activeThread.posts || activeThread.posts.length === 0) ? (
                <p className="text-xs text-slate-500 italic">No replies yet. Share your answer below.</p>
              ) : (
                activeThread.posts.map((post) => (
                  <div
                    key={post.id}
                    className={`p-4 rounded-lg border space-y-2.5 transition ${
                      post.is_endorsed
                        ? "bg-emerald-950/20 border-emerald-600/40 shadow-sm"
                        : "bg-slate-800/30 border-slate-800"
                    }`}
                  >
                    {/* Author & Endorsed Header */}
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200">
                          {post.author?.full_name || post.author?.email}
                        </span>
                        {post.author?.role === "INSTRUCTOR" && (
                          <span className="text-2xs px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 font-bold">
                            INSTRUCTOR
                          </span>
                        )}
                        <span className="text-slate-500">· {new Date(post.created_at).toLocaleDateString()}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        {post.is_endorsed && (
                          <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-2xs font-bold border border-emerald-500/30 flex items-center gap-1">
                            ⭐ Instructor Endorsed
                          </span>
                        )}
                        {isInstructor && (
                          <button
                            onClick={() => handleEndorsePost(post.id)}
                            className="text-2xs font-semibold px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                          >
                            {post.is_endorsed ? "Un-endorse" : "Endorse as Solution"}
                          </button>
                        )}
                        <button
                          onClick={() => handleTogglePostVote(post.id)}
                          className={`px-2 py-0.5 rounded text-2xs font-semibold border ${
                            post.has_upvoted
                              ? "bg-sky-500/20 text-sky-400 border-sky-500/40"
                              : "bg-slate-800 text-slate-400 border-slate-700"
                          }`}
                        >
                          ▲ {post.upvotes_count}
                        </button>
                        <button
                          onClick={() => setReportingTarget({ postId: post.id })}
                          className="text-2xs text-slate-500 hover:text-rose-400"
                        >
                          🚩
                        </button>
                      </div>
                    </div>

                    <div className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {post.body}
                    </div>

                    {/* Nested child replies (1-level down) */}
                    {post.replies && post.replies.length > 0 && (
                      <div className="space-y-2 mt-3 pt-3 border-t border-slate-800/60 pl-4 border-l-2 border-slate-700">
                        {post.replies.map((child) => (
                          <div key={child.id} className="text-xs text-slate-300 space-y-1">
                            <div className="flex items-center gap-2 text-2xs text-slate-400">
                              <strong className="text-slate-200">{child.author?.full_name || child.author?.email}</strong>
                              <span>{new Date(child.created_at).toLocaleDateString()}</span>
                            </div>
                            <p>{child.body}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Reply Input Form */}
            <form onSubmit={handleAddReply} className="space-y-2 pt-2 border-t border-slate-800">
              <textarea
                rows={3}
                placeholder="Write your constructive reply or question..."
                value={replyBody}
                onChange={(e) => setReplyBody(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-lg p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={!replyBody.trim() || isSubmitting}
                  className="px-4 py-2 rounded-lg text-xs font-semibold bg-sky-500 hover:bg-sky-400 text-slate-950 disabled:opacity-40"
                >
                  {isSubmitting ? "Posting..." : "Post Reply"}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* New Thread Modal */}
      {isNewThreadOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="font-bold text-base text-white">Ask a Question / Start Thread</h3>
              <button
                onClick={() => setIsNewThreadOpen(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateThread} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., How does consensus election timeout work in Raft?"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Question Body</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Provide context, code snippets, or specific questions..."
                  value={newBody}
                  onChange={(e) => setNewBody(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsNewThreadOpen(false)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newTitle.trim() || !newBody.trim() || isSubmitting}
                  className="px-5 py-2 rounded-lg text-xs font-semibold bg-sky-500 hover:bg-sky-400 text-slate-950 disabled:opacity-40"
                >
                  {isSubmitting ? "Publishing..." : "Publish Question"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Content Reporting Modal (FR-DIS-04) */}
      {reportingTarget && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="font-bold text-base text-rose-400 flex items-center gap-2">
              🚩 Report Inappropriate Content
            </h3>
            <p className="text-xs text-slate-400">
              Flag content for review by platform moderators. Submissions violating academic integrity or community guidelines will be moderated.
            </p>

            {reportSuccess ? (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs rounded-lg text-center font-semibold">
                ✓ Report submitted to moderator queue.
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Reason</label>
                  <select
                    value={reportReason}
                    onChange={(e) => setReportReason(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white"
                  >
                    <option value="SPAM">Spam or Promotional Advertising</option>
                    <option value="HARASSMENT">Harassment or Hate Speech</option>
                    <option value="ACADEMIC_DISHONESTY">Academic Dishonesty / Sharing Answers</option>
                    <option value="INAPPROPRIATE">Inappropriate or Offensive Material</option>
                    <option value="OFF_TOPIC">Off Topic</option>
                    <option value="OTHER">Other Violation</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Details (Optional)</label>
                  <textarea
                    rows={3}
                    placeholder="Provide additional details for the moderator..."
                    value={reportDetails}
                    onChange={(e) => setReportDetails(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setReportingTarget(null)}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleFileReport}
                    className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white"
                  >
                    Submit Report
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
