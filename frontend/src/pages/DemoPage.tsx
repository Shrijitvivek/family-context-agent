/**
 * DemoPage.tsx
 *
 * Highly efficient, viewport-fitted Judge Mode overview.
 * Styled with clean neutral slates (no purple) and optimized layout.
 */

import { useNavigate } from "react-router-dom";
import {
  FlaskConical,
  ShieldAlert,
  ArrowRight,
  Sparkles,
  Layers,
} from "lucide-react";

import ScenarioPicker from "../components/demo/ScenarioPicker";
import { useFamily } from "../context/FamilyContext";

export default function DemoPage() {
  const navigate = useNavigate();

  const { setSelectedFamilyId } = useFamily();

  const handleLoaded = (familyId: string) => {
    setSelectedFamilyId(familyId);
  };
  return (
    <main className="mx-auto flex h-[calc(100vh-theme(spacing.16))] max-h-screen w-full max-w-[1600px] flex-col justify-between gap-4 overflow-hidden pb-4 font-sans sm:gap-5">
      {/* Page Header Surface */}
      <section className="flex shrink-0 items-center justify-between rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(15,23,42,0.025)]">
        <div className="min-w-0">
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-100 px-3 py-1">
            <Sparkles aria-hidden="true" size={13} className="text-slate-700" />
            <span className="text-xs font-semibold text-slate-800">
              Demo Playground
            </span>
          </div>

          <h1 className="text-2xl font-bold tracking-[-0.04em] text-slate-950 sm:text-3xl">
            Demo Playground
          </h1>

          <p className="mt-1 text-xs text-slate-500 sm:text-sm">
            Load a prepared family scenario and demonstrate the agent
            end-to-end.
          </p>
        </div>

        <div className="hidden items-center gap-2 sm:flex">
          <span className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700">
            <FlaskConical
              size={14}
              aria-hidden="true"
              className="text-slate-600"
            />
            Interactive testing environment
          </span>
        </div>
      </section>

      {/* Intro Card */}
      <section className="flex shrink-0 flex-col justify-between rounded-2xl border border-slate-200/80 bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.025)] sm:p-5">
        <div className="flex items-center gap-3">
          <div className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-800 ring-1 ring-inset ring-slate-200/60">
            <Layers size={18} aria-hidden="true" />
          </div>

          <div className="min-w-0 flex-1">
            <h2 className="text-sm font-semibold tracking-tight text-slate-950 sm:text-base">
              Demo Scenarios
            </h2>
            <p className="mt-0.5 text-xs text-slate-500 leading-relaxed">
              Choose a prepared fictional family scenario to explore the
              application with sample household data.
            </p>
          </div>
        </div>

        <div className="mt-3 flex items-center gap-2 border-t border-slate-100 pt-3 text-[11px] font-medium text-slate-500">
          <ArrowRight
            size={13}
            className="shrink-0 text-slate-700"
            aria-hidden="true"
          />
          <span>
            Once loaded, you'll immediately return to the main dashboard with
            your selected scenario active.
          </span>
        </div>
      </section>

      {/* Scenario Selector */}
      <section
        aria-label="Choose a demo scenario"
        className="min-h-0 flex-1 overflow-y-auto"
      >
        <ScenarioPicker onLoaded={handleLoaded} />
      </section>

      {/* Compact Warning Footer */}
      <aside className="shrink-0 rounded-2xl border border-amber-200/80 bg-amber-50/70 p-3.5 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-amber-200 bg-white text-amber-700">
            <ShieldAlert size={16} aria-hidden="true" />
          </div>

          <div className="min-w-0 flex-1">
            <h2 className="text-xs font-semibold text-amber-950">Demo data</h2>
            <p className="text-[11px] text-amber-900/80 truncate">
              Loading a scenario overrides the current demo household data.
              Intended strictly for testing and live demonstrations.
            </p>
          </div>
        </div>
      </aside>
    </main>
  );
}
