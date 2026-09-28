"use client";

import { useEffect, useState } from "react";
import { ApiError, getRequirementDetail } from "@/lib/api";
import type { RequirementResult } from "@/lib/types";
import CapabilityBadge from "./CapabilityBadge";
import SeverityBadge from "./SeverityBadge";

export default function RequirementDetailPanel({
  jobId,
  requirementId,
  onClose,
}: {
  jobId: string;
  requirementId: string | null;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<RequirementResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!requirementId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setError(null);
    getRequirementDetail(jobId, requirementId)
      .then((d) => {
        if (!cancelled) setDetail(d);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load detail.");
      });
    return () => {
      cancelled = true;
    };
  }, [jobId, requirementId]);

  if (!requirementId) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/30" onClick={onClose}>
      <div
        className="h-full w-full max-w-xl overflow-y-auto bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-gray-900">{requirementId} — Observability</h3>
          <button onClick={onClose} className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600">
            ✕
          </button>
        </div>

        {error && <p className="mt-4 text-sm text-red-700">{error}</p>}
        {!detail && !error && <p className="mt-4 text-sm text-gray-500">Loading...</p>}

        {detail && (
          <div className="mt-4 space-y-5">
            <Section title="1. Requirement">
              <p className="text-sm text-gray-800">{detail.requirement.original_requirement}</p>
              <dl className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-600">
                <Field label="Category" value={detail.requirement.requirement_category} />
                <Field label="Mandatory/Optional" value={detail.requirement.mandatory_or_optional} />
                <Field label="Deadline" value={detail.requirement.deadline_or_timeline || "—"} />
                <Field label="Evidence needed" value={detail.requirement.evidence_needed} />
              </dl>
            </Section>

            <Section title={`2. Retrieved Evidence (${detail.evidence.length})`}>
              {detail.evidence.length === 0 && (
                <p className="text-sm text-gray-500">No evidence retrieved.</p>
              )}
              <div className="space-y-2">
                {detail.evidence.map((e, i) => (
                  <div key={i} className="rounded-md border border-gray-100 bg-gray-50 p-2.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-gray-700">{e.source_document}</span>
                      <span className="text-gray-400">similarity {e.similarity_score}</span>
                    </div>
                    <p className="mt-1 text-gray-600">{e.content}</p>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="3. Capability Assessment">
              <div className="flex items-center gap-2">
                <CapabilityBadge status={detail.assessment.capability_status} />
                <span className="text-xs text-gray-500">
                  confidence {Math.round(detail.assessment.confidence * 100)}%
                </span>
              </div>
              <p className="mt-2 text-sm text-gray-700">{detail.assessment.supporting_evidence}</p>
              {detail.assessment.capability_gap && (
                <p className="mt-1 text-xs text-red-700">Gap: {detail.assessment.capability_gap}</p>
              )}
            </Section>

            <Section title="4. Gap Analysis (deterministic)">
              <div className="flex items-center gap-2">
                <span className="status-pill bg-slate-100 text-slate-700">{detail.gap.gap_type}</span>
                <SeverityBadge severity={detail.gap.severity} />
                {detail.gap.requires_human_review && (
                  <span className="status-pill bg-amber-100 text-amber-800">Human review</span>
                )}
              </div>
              <p className="mt-2 text-sm text-gray-700">{detail.gap.rationale}</p>
            </Section>

            <Section title="5. Draft Response">
              <p className="whitespace-pre-line text-sm text-gray-800">{detail.response.response_text}</p>
              {detail.response.citations.length > 0 && (
                <p className="mt-2 text-xs text-gray-500">
                  Citations: {detail.response.citations.join(", ")}
                </p>
              )}
              {detail.response.requires_human_confirmation && (
                <p className="mt-1 text-xs text-amber-700">
                  Requires human confirmation
                  {detail.response.confirmation_reason ? `: ${detail.response.confirmation_reason}` : "."}
                </p>
              )}
            </Section>

            <Section title="6. Validation">
              <dl className="grid grid-cols-2 gap-2 text-xs">
                <Field label="Requirement addressed" value={detail.validation.requirement_addressed ? "Yes" : "No"} />
                <Field label="Evidence supported" value={detail.validation.evidence_supported ? "Yes" : "No"} />
                <Field label="Citation present" value={detail.validation.citation_present ? "Yes" : "No"} />
                <Field label="Validation score" value={detail.validation.validation_score.toFixed(2)} />
              </dl>
              {detail.validation.unsupported_claims.length > 0 && (
                <p className="mt-2 text-xs text-red-700">
                  Unsupported claims: {detail.validation.unsupported_claims.join("; ")}
                </p>
              )}
              {detail.validation.missing_elements.length > 0 && (
                <p className="mt-1 text-xs text-amber-700">
                  Missing elements: {detail.validation.missing_elements.join("; ")}
                </p>
              )}
              {detail.revision_count > 0 && (
                <p className="mt-2 text-xs text-gray-500">
                  This response went through {detail.revision_count} revision
                  {detail.revision_count === 1 ? "" : "s"} before passing validation.
                </p>
              )}
            </Section>

            <Section title="Node trace">
              <ol className="space-y-1 text-xs text-gray-500">
                {detail.trace.map((t, i) => (
                  <li key={i}>
                    <span className="font-mono text-gray-700">{t.node}</span> — {t.summary}
                  </li>
                ))}
              </ol>
            </Section>
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-gray-100 pt-4 first:border-t-0 first:pt-0">
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">{title}</h4>
      {children}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-gray-400">{label}</dt>
      <dd className="text-gray-700">{value}</dd>
    </div>
  );
}
