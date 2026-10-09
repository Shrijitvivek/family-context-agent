import { useNavigate } from "react-router-dom";
import {
  FlaskConical,
  ShieldAlert,
  ArrowRight,
  Sparkles,
} from "lucide-react";

import PageHeader from "../components/ui/PageHeader";
import ScenarioPicker from "../components/demo/ScenarioPicker";

export default function DemoPage() {
  const navigate = useNavigate();

  const handleLoaded = (familyId: string) => {
    // Store the selected demo family so the normal application
    // screens can use it.
    localStorage.setItem("demo_family_id", familyId);

    navigate("/");
  };

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-7 sm:px-6 sm:py-9 lg:px-8">
      <PageHeader
        title="Judge Mode"
        description="Load a prepared family scenario and demonstrate the agent end-to-end."
      />

      {/* Intro card */}
      <section className="mt-6 rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-50/70 text-violet-600 ring-1 ring-inset ring-violet-100/70">
            <FlaskConical size={21} aria-hidden="true" />
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base font-semibold tracking-tight text-slate-900">
                Demo scenarios
              </h2>

              <span className="inline-flex items-center gap-1 rounded-full border border-violet-100 bg-violet-50/70 px-2 py-1 text-[11px] font-semibold text-violet-700">
                <Sparkles size={12} aria-hidden="true" />
                Judge mode
              </span>
            </div>

            <p className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-500">
              Choose a prepared fictional family scenario to explore the
              application with sample household data and demonstrate the
              agent's capabilities.
            </p>
          </div>
        </div>

        <div className="mt-5 flex items-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
          <ArrowRight
            size={14}
            className="shrink-0 text-violet-500"
            aria-hidden="true"
          />
          <span>
            Once loaded, you'll return to the dashboard with the selected
            scenario.
          </span>
        </div>
      </section>

      {/* Scenario selector */}
      <section aria-label="Choose a demo scenario" className="mt-6">
        <ScenarioPicker onLoaded={handleLoaded} />
      </section>

      {/* Demo environment warning */}
      <aside className="mt-6 rounded-2xl border border-amber-200/80 bg-amber-50/60 p-5 sm:p-6">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-amber-200/80 bg-white/80 text-amber-700">
            <ShieldAlert size={20} aria-hidden="true" />
          </div>

          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-amber-950">
              Demo environment
            </h2>

            <p className="mt-1.5 text-sm leading-6 text-amber-900/80">
              Loading a scenario replaces the existing demo household with
              the selected fictional scenario. Use this mode for
              demonstrations and avoid relying on it for real family data.
            </p>
          </div>
        </div>
      </aside>
    </main>
  );
}