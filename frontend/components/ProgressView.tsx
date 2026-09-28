import type { JobProgress } from "@/lib/types";
import CapabilityBadge from "./CapabilityBadge";

const NODE_LABELS: Record<string, string> = {
  ingest_rfp: "Ingesting RFP",
  extract_requirements: "Extracting requirements",
  classify_requirements: "Classifying requirements",
  retrieve_evidence: "Retrieving evidence",
  assess_capability: "Assessing capability",
  identify_gaps: "Identifying gaps",
  draft_response: "Drafting response",
  validate_response: "Validating response",
  final_output: "Building final analysis",
};

export default function ProgressView({ progress }: { progress: JobProgress }) {
  const pct =
    progress.total_requirements > 0
      ? Math.round((progress.completed_requirements / progress.total_requirements) * 100)
      : 0;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Analysis in progress</h2>
        <span className="status-pill bg-brand-50 text-brand-700">
          {progress.current_node ? NODE_LABELS[progress.current_node] ?? progress.current_node : "Starting..."}
        </span>
      </div>

      {progress.total_requirements > 0 && (
        <>
          <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-brand-500 transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {progress.completed_requirements} of {progress.total_requirements} requirements
            processed
          </p>
        </>
      )}

      {progress.total_requirements === 0 && (
        <p className="mt-4 text-sm text-gray-500">Extracting requirements from the RFP...</p>
      )}

      <ul className="mt-6 divide-y divide-gray-100">
        {progress.requirements.map((r) => (
          <li key={r.requirement_id} className="flex items-center justify-between gap-4 py-2.5">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-gray-900">
                {r.requirement_id} — {r.original_requirement}
              </p>
              <p className="text-xs text-gray-500">{r.category}</p>
            </div>
            {r.node_status === "completed" && <CapabilityBadge status={r.capability_status} />}
            {r.node_status === "in_progress" && (
              <span className="status-pill animate-pulse bg-brand-100 text-brand-700">
                {r.current_node ? NODE_LABELS[r.current_node] ?? r.current_node : "Working..."}
              </span>
            )}
            {r.node_status === "pending" && (
              <span className="status-pill bg-gray-100 text-gray-500">Queued</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
