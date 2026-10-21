import { useEffect, useState } from "react";
import {
  getDemoScenarios,
  loadDemoScenario,
  type ScenarioSummary,
} from "../../services/api/demo";

interface ScenarioPickerProps {
  onLoaded: (familyId: string) => void;
}

export default function ScenarioPicker({
  onLoaded,
}: ScenarioPickerProps) {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenario, setSelectedScenario] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    if (!selectedScenario) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const result = await loadDemoScenario(selectedScenario);

      onLoaded(result.family_id);
    } catch {
      setError("Unable to load the selected scenario.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <h2 className="text-lg font-semibold text-slate-900">
        Choose Demo Scenario
      </h2>

      <p className="mt-2 text-sm text-slate-500">
        Load a fictional family scenario for judge testing.
      </p>

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mt-5 space-y-3">
        {scenarios.map((scenario) => (
          <label
            key={scenario.id}
            className="flex cursor-pointer gap-3 rounded-lg border p-4 hover:bg-slate-50"
          >
            <input
              type="radio"
              name="scenario"
              value={scenario.id}
              checked={selectedScenario === scenario.id}
              onChange={(event) =>
                setSelectedScenario(event.target.value)
              }
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
      </div>

      <button
        type="button"
        disabled={loading || !selectedScenario}
        onClick={handleLoad}
        className="mt-5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {loading ? "Loading..." : "Load Scenario"}
      </button>
    </div>
  );
}