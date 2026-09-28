"use client";

import { useEffect, useState } from "react";
import { ApiError, getEvalResults } from "@/lib/api";
import type { EvalResults } from "@/lib/types";

function pct(v: number | null): string {
  return v === null ? "—" : `${Math.round(v * 100)}%`;
}

export default function EvalMetricsPanel() {
  const [results, setResults] = useState<EvalResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getEvalResults()
      .then(setResults)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load."));
  }, []);

  if (error) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 text-sm text-gray-600 shadow-sm">
        {error}
      </div>
    );
  }

  if (!results) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 text-sm text-gray-500 shadow-sm">
        Loading evaluation results...
      </div>
    );
  }

  const cards = [
    {
      label: "Requirement extraction",
      value: `${results.requirement_extraction.extracted_count} / ${results.requirement_extraction.expected_count}`,
      sub: `field completeness ${pct(results.requirement_extraction.field_completeness_rate)}`,
    },
    {
      label: "Retrieval hit-rate",
      value: pct(results.retrieval.hit_rate),
      sub: `${results.retrieval.cases_evaluated} cases`,
    },
    {
      label: "Capability classification accuracy",
      value: pct(results.capability_classification.accuracy),
      sub: `${results.capability_classification.cases_evaluated} cases`,
    },
    {
      label: "Evidence grounding rate",
      value: pct(results.evidence_grounding.grounding_rate),
      sub: `${results.evidence_grounding.cases_evaluated} cases`,
    },
    {
      label: "Validator recall on flawed drafts",
      value: pct(results.response_validation.recall_on_flawed_drafts),
      sub: `${results.response_validation.cases_evaluated} deliberately-flawed cases`,
    },
  ];

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-500">
        Computed by <code className="rounded bg-gray-100 px-1 py-0.5">eval/run_eval.py</code> against
        the hand-labeled dataset in <code className="rounded bg-gray-100 px-1 py-0.5">eval/dataset.py</code>.
        Model: {results.model}. Last run: {new Date(results.generated_at).toLocaleString()}.
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => (
          <div key={c.label} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-2xl font-bold text-gray-900">{c.value}</p>
            <p className="mt-1 text-xs font-medium text-gray-700">{c.label}</p>
            <p className="text-xs text-gray-400">{c.sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
