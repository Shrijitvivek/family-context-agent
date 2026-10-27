import { useEffect, useState } from "react";
import {
  CheckCircle2,
  Users,
  CalendarCheck,
  Wallet,
  GitBranch,
  Bell,
  X,
  LayoutDashboard,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import {
  getDemoScenarios,
  loadDemoScenario,
  type ScenarioSummary,
  type DemoLoadResult,
} from "../../services/api/demo";

interface ScenarioPickerProps {
  onLoaded: (familyId: string) => void;
}

export default function ScenarioPicker({ onLoaded }: ScenarioPickerProps) {
  const navigate = useNavigate();

  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenario, setSelectedScenario] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadResult, setLoadResult] = useState<DemoLoadResult | null>(null);

  useEffect(() => {
    const loadScenarios = async () => {
      try {
        const data = await getDemoScenarios();
        setScenarios(data);

        if (data.length > 0) {
          setSelectedScenario(data[0].id);
        }
      } catch {
        setError("Unable to load demo scenarios.");
      }
    };

    loadScenarios();
  }, []);

  const handleLoad = async () => {
    if (!selectedScenario) return;

    try {
      setLoading(true);
      setError(null);
      setLoadResult(null);

      const result = await loadDemoScenario(selectedScenario);

      // Save the active demo family without leaving this page.
      localStorage.setItem("demo_family_id", result.family_id);
      onLoaded(result.family_id);

      setLoadResult(result);
    } catch {
      setError("Unable to load the selected scenario. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const closeModal = () => setLoadResult(null);

  return (
    <>
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-slate-900">
          Choose Demo Scenario
        </h2>

        <p className="mt-2 text-sm text-slate-500">
          Load a prepared fictional family to explore Famora AI with sample
          household data.
        </p>

        {error && (
          <div
            role="alert"
            className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700"
          >
            {error}
          </div>
        )}

        <div className="mt-5 space-y-3">
          {scenarios.map((scenario) => (
            <label
              key={scenario.id}
              className={`flex cursor-pointer gap-3 rounded-lg border p-4 transition ${
                selectedScenario === scenario.id
                  ? "border-slate-900 bg-slate-50"
                  : "border-slate-200 hover:bg-slate-50"
              }`}
            >
              <input
                type="radio"
                name="scenario"
                value={scenario.id}
                checked={selectedScenario === scenario.id}
                onChange={(event) => setSelectedScenario(event.target.value)}
                className="mt-1 accent-slate-900"
              />

              <div>
                <div className="font-medium text-slate-900">
                  {scenario.title}
                </div>
                <div className="mt-1 text-sm text-slate-500">
                  {scenario.description}
                </div>
              </div>
            </label>
          ))}

          {scenarios.length === 0 && !error && (
            <p className="text-sm text-slate-500">
              Loading available scenarios...
            </p>
          )}
        </div>

        <button
          type="button"
          disabled={loading || !selectedScenario}
          onClick={handleLoad}
          className="mt-5 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Loading scenario..." : "Load Scenario"}
        </button>
      </div>

      {loadResult && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-950/50 p-4 backdrop-blur-sm"
          onClick={closeModal}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="demo-success-title"
            className="my-auto w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="flex size-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
                  <CheckCircle2 size={26} />
                </div>
                <div>
                  <h2
                    id="demo-success-title"
                    className="text-xl font-bold text-slate-950"
                  >
                    Demo loaded successfully!
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Your selected sample family is ready.
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={closeModal}
                aria-label="Close success popup"
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
              >
                <X size={19} />
              </button>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <SummaryItem
                icon={<Users size={19} />}
                label="Family members"
                value={loadResult.members}
              />
              <SummaryItem
                icon={<CalendarCheck size={19} />}
                label="Commitments"
                value={loadResult.commitments}
              />
              <SummaryItem
                icon={<Wallet size={19} />}
                label="Expense records"
                value={loadResult.expenses}
              />
              <SummaryItem
                icon={<GitBranch size={19} />}
                label="Dependencies"
                value={loadResult.dependencies}
              />
              <div className="col-span-2">
                <SummaryItem
                  icon={<Bell size={19} />}
                  label="Items needing attention"
                  value={loadResult.attention_items}
                />
              </div>
            </div>

            <p className="mt-4 text-xs leading-relaxed text-slate-500">
              These counts reflect the data reported by the backend for this
              scenario. You can now explore the household dashboard.
            </p>

            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={closeModal}
                className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Stay in Demo Playground
              </button>

              <button
                type="button"
                onClick={() => navigate("/")}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700"
              >
                <LayoutDashboard size={17} />
                Explore Dashboard
              </button>
            </div>
          </section>
        </div>
      )}
    </>
  );
}

interface SummaryItemProps {
  icon: React.ReactNode;
  label: string;
  value: number;
}

function SummaryItem({ icon, label, value }: SummaryItemProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-center gap-2 text-slate-600">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <p className="mt-2 text-2xl font-bold tabular-nums text-slate-950">
        {value}
      </p>
    </div>
  );
}
