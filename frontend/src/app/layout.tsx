import "./globals.css";
import React from "react";
import { AuthProvider } from "../context/AuthContext";
import { Navbar } from "../components/Navbar";

export const metadata = {
  title: "FutureLearning Learning Engine",
  description: "Scalable, personalized, accessible online education platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex flex-col min-h-screen bg-slate-50 text-slate-900 antialiased selection:bg-indigo-500 selection:text-white">
        {/* Skip to Main Content Link for WCAG Accessibility */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-indigo-600 focus:text-white focus:rounded-md focus:shadow-lg"
        >
          Skip to main content
        </a>

        <AuthProvider>
          {/* Global Navigation Bar */}
          <Navbar />

          {/* Main Content Landmark */}
          <main id="main-content" className="flex-1 focus:outline-none">
            {children}
          </main>

          {/* Accessible Global Footer */}
          <footer className="border-t border-slate-200/80 bg-white py-10 text-center text-sm text-slate-500">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-2">
              <p className="font-medium text-slate-700">
                FutureLearning Learning Engine · Next.js 15 + Django 5 + Neon PostgreSQL + Redis + Celery
              </p>
              <p className="text-xs text-slate-400">
                Complex Computing Problem (CCP) · University Software Engineering · WCAG 2.1 Level AA Certified
              </p>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
