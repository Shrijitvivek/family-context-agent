import { Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Compass,
  House,
  Search,
} from "lucide-react";

export default function NotFoundPage() {
  return (
    <main className="flex min-h-[calc(100vh-2rem)] items-center justify-center px-5 py-12">
      <section className="w-full max-w-lg text-center">
        {/* Illustration */}
        <div className="relative mx-auto mb-8 flex h-24 w-24 items-center justify-center">
          <div className="absolute inset-0 rotate-6 rounded-[2rem] border border-violet-100 bg-violet-50/70" />

          <div className="relative flex h-20 w-20 items-center justify-center rounded-3xl border border-slate-200 bg-white text-violet-600 shadow-sm">
            <Compass size={38} strokeWidth={1.5} aria-hidden="true" />
          </div>

          <span className="absolute -right-1 -top-1 flex h-8 w-8 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 shadow-sm">
            <Search size={15} aria-hidden="true" />
          </span>
        </div>

        {/* Error code */}
        <p className="text-sm font-semibold tracking-[0.2em] text-violet-600">
          ERROR 404
        </p>

        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
          Page not found
        </h1>

        <p className="mx-auto mt-4 max-w-md text-sm leading-6 text-slate-500 sm:text-base">
          We couldn't find the page you're looking for. It may have been moved,
          removed, or the link might be incorrect.
        </p>

        {/* Actions */}
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            to="/"
            className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2 sm:w-auto"
          >
            <House size={16} aria-hidden="true" />
            Back to dashboard
            <ArrowRight size={15} aria-hidden="true" />
          </Link>

          <button
            type="button"
            onClick={() => window.history.back()}
            className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 focus-visible:ring-offset-2 sm:w-auto"
          >
            <ArrowLeft size={15} aria-hidden="true" />
            Go back
          </button>
        </div>

        {/* Footer */}
        <div className="mt-10 border-t border-slate-200/80 pt-5">
          <p className="text-xs text-slate-400">
            Family Context · Your family's information, all in one place.
          </p>
        </div>
      </section>
    </main>
  );
}