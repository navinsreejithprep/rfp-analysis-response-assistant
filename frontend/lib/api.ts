import type {
  EvalResults,
  FinalAnalysis,
  JobProgress,
  RequirementResult,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON — fall back to statusText
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export async function listKnowledgeBaseDocuments(): Promise<{ documents: string[] }> {
  const res = await fetch(`${API_URL}/api/knowledge-base/documents`, { cache: "no-store" });
  return handle(res);
}

export async function uploadKnowledgeBaseDocuments(
  files: File[]
): Promise<{ added: { filename: string; chunks_indexed: number }[] }> {
  const formData = new FormData();
  for (const f of files) formData.append("files", f);
  const res = await fetch(`${API_URL}/api/knowledge-base/documents`, {
    method: "POST",
    body: formData,
  });
  return handle(res);
}

export async function analyzeRfp(file: File): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/api/rfp/analyze`, {
    method: "POST",
    body: formData,
  });
  return handle(res);
}

export async function getJobProgress(jobId: string): Promise<JobProgress> {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}`, { cache: "no-store" });
  return handle(res);
}

export async function getRequirementDetail(
  jobId: string,
  requirementId: string
): Promise<RequirementResult> {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}/requirements/${requirementId}`, {
    cache: "no-store",
  });
  return handle(res);
}

export async function getFinalAnalysis(jobId: string): Promise<FinalAnalysis> {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}/final`, { cache: "no-store" });
  return handle(res);
}

export function exportUrl(jobId: string): string {
  return `${API_URL}/api/jobs/${jobId}/export`;
}

export async function getEvalResults(): Promise<EvalResults> {
  const res = await fetch(`${API_URL}/api/eval/results`, { cache: "no-store" });
  return handle(res);
}
