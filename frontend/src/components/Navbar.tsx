"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import { AccessibilityControls } from "./AccessibilityControls";
import { NotificationBell } from "./NotificationBell";
import {
  BookOpen,
  LayoutDashboard,
  Sparkles,
  User as UserIcon,
  LogOut,
  ShieldAlert,
  GraduationCap,
} from "lucide-react";

export function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const isInstructorOrAdmin =
    user?.role === "INSTRUCTOR" || user?.role === "ADMIN";

  const navLinks = [
    { href: "/courses", label: "Catalog", icon: BookOpen },
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    ...(isInstructorOrAdmin
      ? [{ href: "/studio", label: "Studio", icon: Sparkles }]
      : []),
    { href: "/smoke-test", label: "System Health", icon: ShieldAlert },
  ];

  return (
    <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-md sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo & Brand */}
        <div className="flex items-center space-x-4">
          <Link
            href="/courses"
            className="flex items-center space-x-2 text-xl font-bold tracking-tight text-indigo-600 hover:text-indigo-700 transition"
          >
            <GraduationCap className="w-7 h-7 text-indigo-600" aria-hidden="true" />
            <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
              FutureLearning
            </span>
          </Link>
          <span className="text-[11px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
            Engine v1.0
          </span>
        </div>

        {/* Navigation Links */}
        <nav
          aria-label="Main Platform Navigation"
          className="hidden md:flex items-center space-x-1"
        >
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive =
              pathname === link.href || pathname?.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700 font-semibold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/70"
                }`}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className="w-4 h-4" aria-hidden="true" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Tools & User Profile */}
        <div className="flex items-center space-x-3">
          <AccessibilityControls />
          {user && <NotificationBell />}

          {user ? (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
              <Link
                href="/profile"
                className="flex items-center space-x-2 p-1.5 rounded-lg hover:bg-slate-100 transition group"
                title="Account Settings & GDPR"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-violet-500 text-white flex items-center justify-center font-bold text-xs shadow-xs">
                  {user.first_name?.[0] || user.email[0].toUpperCase()}
                </div>
                <div className="hidden lg:block text-left">
                  <p className="text-xs font-semibold text-slate-800 leading-tight">
                    {user.first_name ? `${user.first_name} ${user.last_name}` : user.email}
                  </p>
                  <span className="text-[10px] font-medium text-indigo-600 bg-indigo-50 px-1.5 py-0.2 rounded">
                    {user.role}
                  </span>
                </div>
              </Link>

              <button
                onClick={logout}
                aria-label="Log out"
                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Link
                href="/login"
                className="px-3 py-1.5 text-sm font-medium text-slate-700 hover:text-indigo-600 transition"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="px-3.5 py-1.5 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-xs transition"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
