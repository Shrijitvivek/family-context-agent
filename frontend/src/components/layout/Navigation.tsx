/**
 * Navigation
 *
 * Provides the main navigation links for the Family Context application.
 * It connects users to the main product areas and utility tools like Judge Mode.
 *
 * Responsibilities:
 * - Display grouped navigation sections with icons and descriptions.
 * - Highlight the currently active route with visual indicators.
 * - Provide keyboard and screen-reader accessible navigation.
 * - Reuse seamlessly across desktop and mobile layouts.
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

export default function Navigation() {
  return (
    <nav
      aria-label="Main navigation"
      className="flex flex-col gap-6 rounded-2xl bg-violet-50/70 p-3"
    >
      {/* Main navigation */}
      <section aria-labelledby="navigation-main-heading">
        <h2
          id="navigation-main-heading"
          className="mb-2.5 px-3 text-[10px] font-semibold uppercase tracking-[0.15em] text-violet-400"
        >
          Main menu
        </h2>

        <div className="flex flex-col gap-1">
          {navigationItems.map(({ name, path, icon: Icon, description }) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              title={description}
              aria-label={name}
              className={({ isActive }) =>
                [
                  "group relative flex min-h-11 items-center gap-3 rounded-xl px-3.5 py-2.5",
                  "text-sm font-medium transition-all duration-200 ease-out",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 focus-visible:ring-offset-2",
                  isActive
                    ? "bg-violet-100 text-violet-900 shadow-sm ring-1 ring-inset ring-violet-200"
                    : "text-slate-600 hover:bg-white/80 hover:text-violet-900",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span
                      aria-hidden="true"
                      className="absolute bottom-2.5 left-0 top-2.5 w-[3px] rounded-r-full bg-violet-500"
                    />
                  )}

                  <span
                    className={[
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors duration-200",
                      isActive
                        ? "bg-white text-violet-700"
                        : "text-slate-500 group-hover:bg-white group-hover:text-violet-700",
                    ].join(" ")}
                  >
                    <Icon
                      size={19}
                      strokeWidth={isActive ? 2.1 : 1.8}
                      aria-hidden="true"
                    />
                  </span>

                  <span className="min-w-0 flex-1 truncate">{name}</span>

                  {isActive && (
                    <ChevronRight
                      size={15}
                      strokeWidth={2}
                      aria-hidden="true"
                      className="shrink-0 text-violet-600"
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
          className="mb-2.5 px-3 text-[10px] font-semibold uppercase tracking-[0.15em] text-violet-400"
        >
          Tools
        </h2>

        <div className="flex flex-col gap-1">
          {utilityItems.map(({ name, path, icon: Icon, description }) => (
            <NavLink
              key={path}
              to={path}
              title={description}
              className={({ isActive }) =>
                [
                  "group relative flex min-h-11 items-center gap-3 rounded-xl px-3.5 py-2.5",
                  "text-sm font-medium transition-all duration-200 ease-out",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 focus-visible:ring-offset-2",
                  isActive
                    ? "bg-violet-100 text-violet-900 shadow-sm ring-1 ring-inset ring-violet-200"
                    : "text-slate-600 hover:bg-white/80 hover:text-violet-900",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span
                      aria-hidden="true"
                      className="absolute bottom-2.5 left-0 top-2.5 w-[3px] rounded-r-full bg-violet-500"
                    />
                  )}

                  <span
                    className={[
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors duration-200",
                      isActive
                        ? "bg-white text-violet-700"
                        : "text-slate-500 group-hover:bg-white group-hover:text-violet-700",
                    ].join(" ")}
                  >
                    <Icon
                      size={19}
                      strokeWidth={isActive ? 2.1 : 1.8}
                      aria-hidden="true"
                    />
                  </span>

                  <span className="min-w-0 flex-1 truncate">{name}</span>

                  <span
                    className={[
                      "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5",
                      "text-[9px] font-semibold uppercase tracking-wide transition-colors duration-200",
                      isActive
                        ? "border-violet-200 bg-white text-violet-700"
                        : "border-violet-100 bg-white/80 text-violet-500",
                    ].join(" ")}
                  >
                    <Sparkles size={10} aria-hidden="true" />
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
        className="h-px bg-gradient-to-r from-transparent via-violet-200 to-transparent"
      />
    </nav>
  );
}