const STYLES: Record<string, string> = {
  High: "bg-red-100 text-red-800",
  Medium: "bg-amber-100 text-amber-800",
  Low: "bg-slate-200 text-slate-700",
  None: "bg-emerald-100 text-emerald-800",
};

export default function SeverityBadge({ severity }: { severity: string }) {
  return <span className={`status-pill ${STYLES[severity] || STYLES.None}`}>{severity}</span>;
}
