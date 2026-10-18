"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Notification } from "../lib/types";
import { getNotifications, markNotificationRead, markAllNotificationsRead } from "../lib/api";

export function NotificationBell() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const fetchNotifs = async () => {
    try {
      setIsLoading(true);
      const data = await getNotifications();
      setNotifications(data.results || []);
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      // Quiet fail if guest / unauth
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifs();
    // Periodic refresh every 60s
    const interval = setInterval(fetchNotifs, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleMarkRead = async (notif: Notification) => {
    if (!notif.is_read) {
      try {
        await markNotificationRead(notif.id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
        setUnreadCount((c) => Math.max(0, c - 1));
      } catch (err) {
        console.error("Failed to mark notification read:", err);
      }
    }
    setIsOpen(false);
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to mark all notifications read:", err);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-slate-300 hover:text-white rounded-lg hover:bg-slate-800 transition"
        title="Notifications"
        aria-label="View Notifications"
      >
        <span className="text-lg">🔔</span>
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow-sm">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 md:w-96 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl z-50 overflow-hidden text-slate-100">
          <div className="p-3 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
            <h4 className="font-bold text-xs uppercase tracking-wider text-slate-300">
              Notifications {unreadCount > 0 && `(${unreadCount})`}
            </h4>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-2xs font-semibold text-sky-400 hover:text-sky-300"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/60">
            {notifications.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">
                No notifications right now.
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  onClick={() => handleMarkRead(n)}
                  className={`p-3.5 hover:bg-slate-800/60 transition cursor-pointer flex items-start gap-3 ${
                    !n.is_read ? "bg-slate-800/30" : ""
                  }`}
                >
                  <span className="text-base mt-0.5">
                    {n.notification_type === "ANSWER_ENDORSED"
                      ? "⭐"
                      : n.notification_type === "FORUM_REPLY"
                      ? "💬"
                      : n.notification_type === "ASSESSMENT_GRADED"
                      ? "📝"
                      : "📢"}
                  </span>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <h5 className="font-semibold text-xs text-slate-200">{n.title}</h5>
                      <span className="text-3xs text-slate-500">
                        {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-2xs text-slate-400 leading-snug">{n.message}</p>
                    {n.action_url && (
                      <Link
                        href={n.action_url}
                        className="text-3xs text-sky-400 hover:underline block pt-0.5"
                      >
                        View details →
                      </Link>
                    )}
                  </div>
                  {!n.is_read && (
                    <span className="w-2 h-2 rounded-full bg-sky-400 mt-1.5 flex-shrink-0" />
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
