import type { RequirementResult } from "@/lib/types";
import CapabilityBadge from "./CapabilityBadge";

export default function RequirementMatrix({
  results,
  onSelect,
}: {
  results: RequirementResult[];
  onSelect: (requirementId: string) => void;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              {["ID", "Requirement", "Category", "Capability", "Evidence", "Gap", "Review?"].map((h) => (
                <th
                  key={h}
                  className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {results.map((r) => (
              <tr
                key={r.requirement.requirement_id}
                onClick={() => onSelect(r.requirement.requirement_id)}
                className="cursor-pointer hover:bg-gray-50"
              >
                <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-gray-500">
                  {r.requirement.requirement_id}
                </td>
                <td className="max-w-sm px-4 py-3 text-gray-900">
                  <p className="line-clamp-2">{r.requirement.original_requirement}</p>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                  {r.requirement.requirement_category}
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <CapabilityBadge status={r.assessment.capability_status} />
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                  {r.assessment.source_documents.length} doc
                  {r.assessment.source_documents.length === 1 ? "" : "s"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-gray-600">{r.gap.gap_type}</td>
                <td className="whitespace-nowrap px-4 py-3">
                  {r.gap.requires_human_review ? (
                    <span className="status-pill bg-amber-100 text-amber-800">Yes</span>
                  ) : (
                    <span className="status-pill bg-gray-100 text-gray-500">No</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
