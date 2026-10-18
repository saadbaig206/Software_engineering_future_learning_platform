"use client";

import React, { useState, useEffect } from "react";
import {
  Assessment,
  Question,
  Choice,
  GradeSummary,
  QuizAttempt,
} from "../lib/types";
import { startQuizAttempt, submitQuizAttempt } from "../lib/api";

interface AssessmentPlayerProps {
  assessment: Assessment;
  onCompleted?: (result: GradeSummary) => void;
}

export function AssessmentPlayer({ assessment, onCompleted }: AssessmentPlayerProps) {
  const [activeAttempt, setActiveAttempt] = useState<QuizAttempt | null>(null);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [gradeResult, setGradeResult] = useState<GradeSummary | null>(null);
  const [timeRemainingSeconds, setTimeRemainingSeconds] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Initialize or resume attempt
  const handleStartAttempt = async () => {
    try {
      setErrorMsg(null);
      const attempt = await startQuizAttempt(assessment.id);
      setActiveAttempt(attempt);
      setGradeResult(null);
      setAnswers({});
      setCurrentQuestionIndex(0);

      if (assessment.time_limit_minutes > 0) {
        setTimeRemainingSeconds(assessment.time_limit_minutes * 60);
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Could not start quiz attempt.");
    }
  };

  // Timer countdown
  useEffect(() => {
    if (timeRemainingSeconds === null || timeRemainingSeconds <= 0 || gradeResult) return;

    const timer = setInterval(() => {
      setTimeRemainingSeconds((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(timer);
          // Auto submit when time runs out
          handleSubmitAnswers();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemainingSeconds, gradeResult]);

  const questions = assessment.questions || [];
  const currentQuestion: Question | undefined = questions[currentQuestionIndex];

  const handleSelectChoice = (questionId: string, choiceId: string, isMultiple: boolean) => {
    if (isMultiple) {
      const currentSelected: string[] = answers[questionId] || [];
      const updated = currentSelected.includes(choiceId)
        ? currentSelected.filter((id) => id !== choiceId)
        : [...currentSelected, choiceId];
      setAnswers({ ...answers, [questionId]: updated });
    } else {
      setAnswers({ ...answers, [questionId]: choiceId });
    }
  };

  const handleTextChange = (questionId: string, text: string) => {
    setAnswers({ ...answers, [questionId]: text });
  };

  const handleSubmitAnswers = async () => {
    if (!activeAttempt || isSubmitting) return;

    try {
      setIsSubmitting(true);
      setErrorMsg(null);
      const summary = await submitQuizAttempt(activeAttempt.id, answers);
      setGradeResult(summary);
      setActiveAttempt(null);
      if (onCompleted) {
        onCompleted(summary);
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Error submitting quiz answers.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  // State 1: Before Starting Attempt
  if (!activeAttempt && !gradeResult) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="inline-block px-2.5 py-0.5 text-xs font-semibold rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 mb-2">
              Checkpoint Assessment
            </div>
            <h3 className="text-xl font-bold">{assessment.title}</h3>
            {assessment.description && (
              <p className="text-slate-400 text-sm mt-1">{assessment.description}</p>
            )}
          </div>
          <div className="flex items-center gap-3">
            {assessment.has_passed && (
              <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold rounded-full flex items-center gap-1.5">
                ✓ Passed ({assessment.highest_score}%)
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-6">
          <div className="bg-slate-800/50 p-3.5 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 block">Questions</span>
            <span className="text-lg font-bold text-slate-100">{questions.length} items</span>
          </div>
          <div className="bg-slate-800/50 p-3.5 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 block">Passing Threshold</span>
            <span className="text-lg font-bold text-emerald-400">{assessment.passing_score_percent}%</span>
          </div>
          <div className="bg-slate-800/50 p-3.5 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 block">Time Limit</span>
            <span className="text-lg font-bold text-slate-100">
              {assessment.time_limit_minutes > 0 ? `${assessment.time_limit_minutes} min` : "Untimed"}
            </span>
          </div>
          <div className="bg-slate-800/50 p-3.5 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 block">Attempts Allowed</span>
            <span className="text-lg font-bold text-amber-400">
              {assessment.attempts_used} / {assessment.max_attempts}
            </span>
          </div>
        </div>

        {errorMsg && (
          <div className="p-3 mb-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            {errorMsg}
          </div>
        )}

        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-slate-500">
            {assessment.attempts_remaining > 0
              ? `${assessment.attempts_remaining} attempt(s) remaining`
              : "No attempts remaining."}
          </span>
          <button
            onClick={handleStartAttempt}
            disabled={assessment.attempts_remaining <= 0}
            className="px-6 py-2.5 rounded-lg font-semibold text-sm bg-sky-500 hover:bg-sky-400 text-slate-950 transition disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-sky-500/20"
          >
            {assessment.attempts_used > 0 ? "Retake Assessment" : "Begin Assessment"}
          </button>
        </div>
      </div>
    );
  }

  // State 2: Taking the Assessment (Active Attempt)
  if (activeAttempt && currentQuestion) {
    const isMultiple = currentQuestion.question_type === "MULTIPLE_CHOICE";
    const selectedAnswer = answers[currentQuestion.id];

    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white shadow-xl">
        {/* Progress & Timer Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-6">
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Question {currentQuestionIndex + 1} of {questions.length}
            </span>
            <h4 className="text-base font-bold text-slate-200">
              {assessment.title} · Attempt #{activeAttempt.attempt_number}
            </h4>
          </div>
          {timeRemainingSeconds !== null && (
            <div
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-bold flex items-center gap-1.5 ${
                timeRemainingSeconds < 120
                  ? "bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-pulse"
                  : "bg-slate-800 text-sky-400 border border-slate-700"
              }`}
            >
              ⏱ {formatTime(timeRemainingSeconds)}
            </div>
          )}
        </div>

        {/* Question Prompt */}
        <div className="mb-6">
          <p className="text-lg text-slate-100 font-medium leading-relaxed">
            {currentQuestion.prompt}
          </p>
          <span className="inline-block mt-2 text-xs font-semibold text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
            {currentQuestion.points} point{currentQuestion.points > 1 ? "s" : ""}
          </span>
        </div>

        {/* Question Choices / Input Area */}
        <div className="space-y-3 mb-8">
          {currentQuestion.question_type === "SHORT_ANSWER" ? (
            <div>
              <input
                type="text"
                value={selectedAnswer || ""}
                onChange={(e) => handleTextChange(currentQuestion.id, e.target.value)}
                placeholder="Type your concise answer here..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>
          ) : currentQuestion.question_type === "CODE_SNIPPET" ? (
            <div className="space-y-2">
              <span className="text-xs font-mono text-slate-400 block">
                Language: {currentQuestion.code_language || "python"}
              </span>
              <textarea
                rows={4}
                value={selectedAnswer !== undefined ? selectedAnswer : currentQuestion.initial_code || ""}
                onChange={(e) => handleTextChange(currentQuestion.id, e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-sm text-sky-300 focus:outline-none focus:border-sky-500"
                placeholder="Write your code solution..."
              />
            </div>
          ) : (
            currentQuestion.choices.map((choice) => {
              const isChecked = isMultiple
                ? Array.isArray(selectedAnswer) && selectedAnswer.includes(choice.id)
                : selectedAnswer === choice.id;

              return (
                <label
                  key={choice.id}
                  className={`flex items-center gap-3 p-3.5 rounded-lg border cursor-pointer transition ${
                    isChecked
                      ? "bg-sky-500/10 border-sky-500 text-white shadow-sm"
                      : "bg-slate-800/40 border-slate-800 hover:border-slate-700 text-slate-300"
                  }`}
                >
                  <input
                    type={isMultiple ? "checkbox" : "radio"}
                    name={`q-${currentQuestion.id}`}
                    checked={isChecked}
                    onChange={() => handleSelectChoice(currentQuestion.id, choice.id, isMultiple)}
                    className="w-4 h-4 text-sky-500 focus:ring-sky-500 rounded border-slate-700 bg-slate-900"
                  />
                  <span className="text-sm font-medium">{choice.text}</span>
                </label>
              );
            })
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <button
            type="button"
            onClick={() => setCurrentQuestionIndex((prev) => Math.max(0, prev - 1))}
            disabled={currentQuestionIndex === 0}
            className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            ← Previous
          </button>

          <div className="flex gap-1.5">
            {questions.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentQuestionIndex(idx)}
                className={`w-7 h-7 rounded text-xs font-semibold transition ${
                  idx === currentQuestionIndex
                    ? "bg-sky-500 text-slate-950"
                    : answers[questions[idx].id] !== undefined
                    ? "bg-slate-700 text-white"
                    : "bg-slate-800 text-slate-500"
                }`}
              >
                {idx + 1}
              </button>
            ))}
          </div>

          {currentQuestionIndex < questions.length - 1 ? (
            <button
              type="button"
              onClick={() => setCurrentQuestionIndex((prev) => Math.min(questions.length - 1, prev + 1))}
              className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-950 bg-sky-500 hover:bg-sky-400"
            >
              Next →
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmitAnswers}
              disabled={isSubmitting}
              className="px-5 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 shadow-lg shadow-emerald-600/20"
            >
              {isSubmitting ? "Scoring..." : "Submit for Grading"}
            </button>
          )}
        </div>
      </div>
    );
  }

  // State 3: Graded Result View
  if (gradeResult) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white shadow-xl">
        {/* Results Header */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-5 rounded-xl bg-slate-800/40 border border-slate-800 mb-6">
          <div className="flex items-center gap-4">
            <div
              className={`w-14 h-14 rounded-full flex items-center justify-center font-bold text-xl border-2 ${
                gradeResult.passed
                  ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                  : "bg-rose-500/10 border-rose-500 text-rose-400"
              }`}
            >
              {Math.round(gradeResult.score_percent)}%
            </div>
            <div>
              <h3 className="text-lg font-bold">
                {gradeResult.passed ? "Assessment Passed! 🎉" : "Assessment Completed"}
              </h3>
              <p className="text-xs text-slate-400">
                Earned {gradeResult.points_earned} of {gradeResult.points_possible} points · Passing Score: {gradeResult.passing_score_percent}%
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            {gradeResult.attempts_remaining > 0 && (
              <button
                onClick={handleStartAttempt}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-lg text-slate-200"
              >
                Retake Quiz ({gradeResult.attempts_remaining} left)
              </button>
            )}
          </div>
        </div>

        {/* Detailed Question Review & Explanations (FR-ASM-04) */}
        <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
          Detailed Feedback & Explanations
        </h4>
        <div className="space-y-4">
          {gradeResult.questions.map((q, idx) => (
            <div
              key={q.question_id}
              className={`p-4 rounded-lg border ${
                q.is_correct
                  ? "bg-emerald-950/20 border-emerald-800/30"
                  : "bg-rose-950/20 border-rose-800/30"
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="text-sm font-semibold text-slate-200">
                  {idx + 1}. {q.prompt}
                </span>
                <span
                  className={`px-2 py-0.5 text-xs font-bold rounded ${
                    q.is_correct
                      ? "bg-emerald-500/20 text-emerald-400"
                      : "bg-rose-500/20 text-rose-400"
                  }`}
                >
                  {q.awarded_points}/{q.points_possible} pts
                </span>
              </div>

              {q.explanation && (
                <div className="mt-3 p-3 rounded bg-slate-900/60 border border-slate-800 text-xs text-slate-300">
                  <strong className="text-sky-400 block mb-1">Pedagogical Explanation:</strong>
                  {q.explanation}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return null;
}
