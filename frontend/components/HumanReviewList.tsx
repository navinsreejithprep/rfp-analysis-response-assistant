import type { HumanReviewItem } from "@/lib/types";

const CATEGORY_STYLES: Record<HumanReviewItem["category"], string> = {
  "Unsupported Claim": "bg-red-100 text-red-800",
  "Missing Evidence": "bg-slate-200 text-slate-700",
  "Ambiguous Requirement": "bg-purple-100 text-purple-800",
  "Confirmation Needed": "bg-amber-100 text-amber-800",
};

export default function HumanReviewList({ items }: { items: HumanReviewItem[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 text-sm text-gray-600 shadow-sm">
        Nothing flagged for human review.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <ul className="divide-y divide-gray-100">
        {items.map((item, i) => (
          <li key={`${item.requirement_id}-${i}`} className="flex items-start gap-3 px-4 py-3">
            <span className={`status-pill shrink-0 ${CATEGORY_STYLES[item.category]}`}>
              {item.category}
            </span>
            <div className="min-w-0">
              <p className="font-mono text-xs text-gray-500">{item.requirement_id}</p>
              <p className="text-sm text-gray-800">{item.reason}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
