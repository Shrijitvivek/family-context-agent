/**
 * Card
 *
 * Provides a reusable content container for the Family Context application.
 *
 * Responsibilities:
 * - Give sections a consistent background and border.
 * - Provide consistent padding and rounded corners.
 * - Allow different pages to reuse the same visual container.
 */

import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export default function Card({ children, className = "" }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}