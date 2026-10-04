/**
 * DemoPage
 *
 * Provides the Judge Mode page for demonstrating the Family Context Agent.
 *
 * Responsibilities:
 * - Provide a dedicated route for Judge Mode.
 * - Serve as the foundation for future demo scenarios.
 * - Keep demo functionality separate from the main application pages.
 */

import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";

export default function DemoPage() {
  return (
    <div>
      <PageHeader
        title="Judge Mode"
        description="Demonstrate the main capabilities of the Family Context Agent."
      />

      <Card>
        <h2 className="text-lg font-semibold text-slate-900">
          Demo Mode
        </h2>

        <p className="mt-2 text-sm text-slate-500">
          Demo scenarios will be added here as the agent integration is
          completed.
        </p>
      </Card>
    </div>
  );
}