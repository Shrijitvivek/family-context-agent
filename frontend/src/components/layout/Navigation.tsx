/**
 * Navigation
 *
 * Provides the main navigation links for the Family Context application.
 * It connects users to the five main product areas and Judge Mode.
 *
 * Responsibilities:
 * - Display navigation links with icons.
 * - Highlight the currently active page.
 * - Provide keyboard-focus-friendly navigation.
 * - Reuse the same navigation component on desktop and mobile.
 */

import { NavLink } from "react-router-dom";
import {
  Home,
  MessageCircle,
  Clock3,
  Receipt,
  FileText,
  FlaskConical,
} from "lucide-react";

const navigationItems = [
  { name: "Home", path: "/", icon: Home },
  { name: "Chat", path: "/chat", icon: MessageCircle },
  { name: "Timeline", path: "/timeline", icon: Clock3 },
  { name: "Expenses", path: "/expenses", icon: Receipt },
  { name: "Documents", path: "/documents", icon: FileText },
  { name: "Judge Mode", path: "/demo", icon: FlaskConical },
];

export default function Navigation() {
  return (
    <nav className="flex flex-col gap-2">
      {navigationItems.map(({ name, path, icon: Icon }) => (
        <NavLink
          key={path}
          to={path}
          end={path === "/"}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition ${
              isActive
                ? "bg-slate-900 text-white"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`
          }
        >
          <Icon size={20} />
          <span>{name}</span>
        </NavLink>
      ))}
    </nav>
  );
}