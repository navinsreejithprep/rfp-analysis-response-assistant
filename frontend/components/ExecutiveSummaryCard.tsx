import type { ExecutiveSummary } from "@/lib/types";

const STAT_STYLES: { key: keyof ExecutiveSummary; label: string; color: string }[] = [
  { key: "fully_supported", label: "Fully Supported", color: "text-emerald-700 bg-emerald-50" },
  { key: "partially_supported", label: "Partially Supported", color: "text-amber-700 bg-amber-50" },
  { key: "not_supported", label: "Not Supported", color: "text-red-700 bg-red-50" },
  { key: "insufficient_evidence", label: "Insufficient Evidence", color: "text-slate-700 bg-slate-100" },
];

export default function ExecutiveSummaryCard({ summary }: { summary: ExecutiveSummary }) {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-base font-semibold text-gray-900">Executive Summary</h2>
          <div className="text-right">
            <p className="text-3xl font-bold text-brand-600">{summary.overall_coverage_pct}%</p>
            <p className="text-xs text-gray-500">overall coverage</p>
          </div>
        </div>
        <p className="mt-3 text-sm leading-relaxed text-gray-700">{summary.narrative}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm">
          <p className="text-2xl font-bold text-gray-900">{summary.total_requirements}</p>
          <p className="text-xs text-gray-500">Total Requirements</p>
        </div>
        {STAT_STYLES.map(({ key, label, color }) => (
          <div key={key} className={`rounded-xl border border-gray-200 p-4 text-center shadow-sm ${color}`}>
            <p className="text-2xl font-bold">{summary[key] as number}</p>
            <p className="text-xs">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
