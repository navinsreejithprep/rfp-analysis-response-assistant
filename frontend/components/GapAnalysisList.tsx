import type { RequirementResult } from "@/lib/types";
import SeverityBadge from "./SeverityBadge";

export default function GapAnalysisList({ results }: { results: RequirementResult[] }) {
  const gaps = results.filter((r) => r.gap.gap_type !== "None");

  if (gaps.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 text-sm text-gray-600 shadow-sm">
        No capability or evidence gaps were identified.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {gaps.map((r) => (
        <div key={r.requirement.requirement_id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-mono text-xs text-gray-500">{r.requirement.requirement_id}</p>
            <div className="flex items-center gap-2">
              <span className="status-pill bg-slate-100 text-slate-700">{r.gap.gap_type}</span>
              <SeverityBadge severity={r.gap.severity} />
            </div>
          </div>
          <p className="mt-2 text-sm font-medium text-gray-900">{r.requirement.original_requirement}</p>
          <p className="mt-1 text-sm text-gray-600">{r.gap.rationale}</p>
          {r.assessment.recommended_action && (
            <p className="mt-2 text-xs text-gray-500">
              <span className="font-semibold">Recommended action: </span>
              {r.assessment.recommended_action}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
