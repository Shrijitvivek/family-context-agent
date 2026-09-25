/**
 * AppShell
 *
 * Provides the shared application layout used across the Family Context
 * frontend.
 *
 * Responsibilities:
 * - Provide the desktop sidebar navigation.
 * - Provide responsive mobile navigation.
 * - Provide the common page layout and spacing.
 * - Render the current page inside the shared application frame.
 */

import { useState } from "react";
import { Menu, X } from "lucide-react";
import Navigation from "./Navigation";

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Desktop Sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block">
        <div className="flex h-full flex-col">
          <div className="border-b border-slate-200 px-6 py-5">
            <h1 className="text-xl font-bold">Family Context</h1>
            <p className="mt-1 text-sm text-slate-500">
              Family assistant
            </p>
          </div>

          <div className="flex-1 px-4 py-6">
            <Navigation />
          </div>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-4 lg:hidden">
        <div>
          <h1 className="text-lg font-bold">Family Context</h1>
        </div>

        <button
          type="button"
          onClick={() => setMobileMenuOpen((open) => !open)}
          className="rounded-lg p-2 text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-400"
          aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </header>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="border-b border-slate-200 bg-white px-4 py-4 lg:hidden">
          <Navigation />

          <button
            type="button"
            onClick={() => setMobileMenuOpen(false)}
            className="mt-4 w-full rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Close Menu
          </button>
        </div>
      )}

      {/* Main Content */}
      <main className="min-h-screen lg:ml-64">
        <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}