"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, exportUrl, getFinalAnalysis, getJobProgress } from "@/lib/api";
import type { FinalAnalysis, JobProgress } from "@/lib/types";
import ProgressView from "@/components/ProgressView";
import ExecutiveSummaryCard from "@/components/ExecutiveSummaryCard";
import RequirementMatrix from "@/components/RequirementMatrix";
import GapAnalysisList from "@/components/GapAnalysisList";
import HumanReviewList from "@/components/HumanReviewList";
import RequirementDetailPanel from "@/components/RequirementDetailPanel";
import EvalMetricsPanel from "@/components/EvalMetricsPanel";

const POLL_INTERVAL_MS = 1500;

type Tab = "summary" | "matrix" | "gaps" | "response" | "review" | "eval";

const TABS: { id: Tab; label: string }[] = [
  { id: "summary", label: "Executive Summary" },
  { id: "matrix", label: "Requirement Matrix" },
  { id: "gaps", label: "Capability Gaps" },
  { id: "response", label: "Draft Response" },
  { id: "review", label: "Human Review" },
  { id: "eval", label: "Evaluation" },
];

export default function AnalysisPage({ params }: { params: { jobId: string } }) {
  const { jobId } = params;
  const [progress, setProgress] = useState<JobProgress | null>(null);
  const [finalAnalysis, setFinalAnalysis] = useState<FinalAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("summary");
  const [selectedRequirement, setSelectedRequirement] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const p = await getJobProgress(jobId);
        if (cancelled) return;
        setProgress(p);
        setError(null);

        if (p.status === "completed") {
          if (pollRef.current) clearInterval(pollRef.current);
          const final = await getFinalAnalysis(jobId);
          if (!cancelled) setFinalAnalysis(final);
        } else if (p.status === "error") {
          if (pollRef.current) clearInterval(pollRef.current);
          setError(p.error || "Analysis failed.");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not reach the backend API.");
        }
      }
    }

    poll();
    pollRef.current = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [jobId]);

  if (error) {
    return (
      <main>
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          <p className="font-semibold">Analysis failed</p>
          <p className="mt-1">{error}</p>
        </div>
      </main>
    );
  }

  if (!progress) {
    return (
      <main>
        <p className="text-sm text-gray-500">Loading job status...</p>
      </main>
    );
  }

  if (progress.status !== "completed" || !finalAnalysis) {
    return (
      <main>
        <ProgressView progress={progress} />
      </main>
    );
  }

  return (
    <main className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">RFP Analysis Dashboard</h1>
          <p className="text-xs text-gray-500">Job {jobId}</p>
        </div>
        <a
          href={exportUrl(jobId)}
          className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Export (.md)
        </a>
      </div>

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex gap-4 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`whitespace-nowrap border-b-2 px-1 py-2.5 text-sm font-medium ${
                tab === t.id
                  ? "border-brand-500 text-brand-600"
                  : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {tab === "summary" && <ExecutiveSummaryCard summary={finalAnalysis.executive_summary} />}

      {tab === "matrix" && (
        <RequirementMatrix
          results={finalAnalysis.requirement_results}
          onSelect={setSelectedRequirement}
        />
      )}

      {tab === "gaps" && <GapAnalysisList results={finalAnalysis.requirement_results} />}

      {tab === "response" && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="prose prose-sm max-w-none whitespace-pre-line text-gray-800">
            {finalAnalysis.consolidated_response}
          </div>
        </div>
      )}

      {tab === "review" && <HumanReviewList items={finalAnalysis.human_review_items} />}

      {tab === "eval" && <EvalMetricsPanel />}

      <RequirementDetailPanel
        jobId={jobId}
        requirementId={selectedRequirement}
        onClose={() => setSelectedRequirement(null)}
      />
    </main>
  );
}
