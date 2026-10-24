/**
 * Navigation.tsx
 *
 * Provides the main navigation links for the Family Context application.
 * Updated with optimized compact sizing and clean line heights.
 * Supports an optional `onNavigate` callback so the parent can auto-close
 * the mobile menu after a link is clicked.
 */

import { NavLink } from "react-router-dom";
import {
  Home,
  MessageCircle,
  Clock3,
  Receipt,
  FileText,
  FlaskConical,
  ChevronRight,
  Sparkles,
} from "lucide-react";

const navigationItems = [
  { name: "Home", path: "/", icon: Home, description: "Family dashboard" },
  { name: "Chat", path: "/chat", icon: MessageCircle, description: "Chat with your family assistant" },
  { name: "Timeline", path: "/timeline", icon: Clock3, description: "Family commitments and events" },
  { name: "Expenses", path: "/expenses", icon: Receipt, description: "Household spending" },
  { name: "Documents", path: "/documents", icon: FileText, description: "Family documents" },
];

const utilityItems = [
  { name: "Judge Mode", path: "/demo", icon: FlaskConical, description: "Load a demo family scenario" },
];

type NavigationProps = {
  /** Called after a link is clicked, so the parent can close the mobile menu. */
  onNavigate?: () => void;
};

export default function Navigation({ onNavigate }: NavigationProps) {
  return (
    <nav
      aria-label="Main navigation"
      className="flex flex-col gap-4 rounded-2xl border border-slate-200/80 bg-white p-2.5 shadow-[0_2px_8px_rgba(15,23,42,0.025)]"
    >
      {/* Main navigation */}
      <section aria-labelledby="navigation-main-heading">
        <h2
          id="navigation-main-heading"
          className="mb-2 px-2.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400"
        >
          Main menu
        </h2>

        <div className="flex flex-col gap-0.5">
          {navigationItems.map(({ name, path, icon: Icon, description }) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              title={description}
              aria-label={name}
              onClick={onNavigate}
              className={({ isActive }) =>
                [
                  "group relative flex min-h-9 items-center gap-2.5 rounded-xl px-3 py-2",
                  "text-xs font-medium leading-relaxed transition-all duration-200 ease-out",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-2",
                  isActive
                    ? "bg-slate-100/80 text-slate-950 font-semibold shadow-xs"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span
                      aria-hidden="true"
                      className="absolute bottom-2 left-0 top-2 w-[3px] rounded-r-full bg-slate-900"
                    />
                  )}

                  <span
                    className={[
                      "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-colors duration-200",
                      isActive
                        ? "bg-slate-900 text-white shadow-xs"
                        : "bg-slate-100 text-slate-500 group-hover:bg-slate-200 group-hover:text-slate-900",
                    ].join(" ")}
                  >
                    <Icon
                      size={16}
                      strokeWidth={isActive ? 2.2 : 1.8}
                      aria-hidden="true"
                    />
                  </span>

                  <span className="min-w-0 flex-1 truncate">{name}</span>

                  {isActive && (
                    <ChevronRight
                      size={14}
                      strokeWidth={2.2}
                      aria-hidden="true"
                      className="shrink-0 text-slate-900"
                    />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </section>

      {/* Tools */}
      <section aria-labelledby="navigation-tools-heading">
        <h2
          id="navigation-tools-heading"
          className="mb-2 px-2.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400"
        >
          Tools
        </h2>

        <div className="flex flex-col gap-0.5">
          {utilityItems.map(({ name, path, icon: Icon, description }) => (
            <NavLink
              key={path}
              to={path}
              title={description}
              onClick={onNavigate}
              className={({ isActive }) =>
                [
                  "group relative flex min-h-9 items-center gap-2.5 rounded-xl px-3 py-2",
                  "text-xs font-medium leading-relaxed transition-all duration-200 ease-out",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-2",
                  isActive
                    ? "bg-slate-100/80 text-slate-950 font-semibold shadow-xs"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span
                      aria-hidden="true"
                      className="absolute bottom-2 left-0 top-2 w-[3px] rounded-r-full bg-slate-900"
                    />
                  )}

                  <span
                    className={[
                      "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-colors duration-200",
                      isActive
                        ? "bg-slate-900 text-white shadow-xs"
                        : "bg-slate-100 text-slate-500 group-hover:bg-slate-200 group-hover:text-slate-900",
                    ].join(" ")}
                  >
                    <Icon
                      size={16}
                      strokeWidth={isActive ? 2.2 : 1.8}
                      aria-hidden="true"
                    />
                  </span>

                  <span className="min-w-0 flex-1 truncate">{name}</span>

                  <span
                    className={[
                      "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5",
                      "text-[9px] font-semibold uppercase tracking-wide transition-colors duration-200",
                      isActive
                        ? "border-slate-300 bg-white text-slate-900 shadow-xs"
                        : "border-slate-200 bg-slate-50 text-slate-500 group-hover:border-slate-300 group-hover:text-slate-700",
                    ].join(" ")}
                  >
                    <Sparkles size={9} aria-hidden="true" />
                    Demo
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </section>

      {/* Bottom divider */}
      <div
        aria-hidden="true"
        className="h-px bg-slate-100 my-0.5"
      />
    </nav>
  );
}