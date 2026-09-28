import type { CapabilityStatus } from "@/lib/types";

const STYLES: Record<CapabilityStatus, string> = {
  "Fully Supported": "bg-emerald-100 text-emerald-800",
  "Partially Supported": "bg-amber-100 text-amber-800",
  "Not Supported": "bg-red-100 text-red-800",
  "Insufficient Evidence": "bg-slate-200 text-slate-700",
};

export default function CapabilityBadge({ status }: { status: CapabilityStatus | null }) {
  if (!status) {
    return <span className="status-pill bg-gray-100 text-gray-500">Pending</span>;
  }
  return <span className={`status-pill ${STYLES[status]}`}>{status}</span>;
}
