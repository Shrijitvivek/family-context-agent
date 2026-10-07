import { useNavigate } from "react-router-dom";
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
    <div>
      <PageHeader
        title="Judge Mode"
        description="Load a prepared family scenario and demonstrate the agent end-to-end."
      />

      <ScenarioPicker onLoaded={handleLoaded} />

      <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-5">
        <h2 className="font-semibold text-amber-900">
          Demo environment
        </h2>

        <p className="mt-2 text-sm text-amber-800">
          Loading a scenario replaces the existing demo household
          with the selected fictional scenario.
        </p>
      </div>
    </div>
  );
}