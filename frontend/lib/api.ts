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

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Render's free tier spins the backend down after ~15 minutes idle; the first
// request after that either fails outright (connection refused) or gets a
// 502/503/504 from Render's proxy while the container is still starting,
// which can take 30-60s. Retry with backoff instead of surfacing a hard
// error on what is usually just a cold start, not an actual outage.
const RETRY_DELAYS_MS = [1500, 3000, 6000, 8000, 8000, 8000];

async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  onRetry?: (attempt: number, maxAttempts: number) => void
): Promise<Response> {
  for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
    try {
      const res = await fetch(url, options);
      if ([502, 503, 504].includes(res.status) && attempt < RETRY_DELAYS_MS.length) {
        onRetry?.(attempt + 1, RETRY_DELAYS_MS.length);
        await sleep(RETRY_DELAYS_MS[attempt]);
        continue;
      }
      return res;
    } catch (err) {
      if (attempt < RETRY_DELAYS_MS.length) {
        onRetry?.(attempt + 1, RETRY_DELAYS_MS.length);
        await sleep(RETRY_DELAYS_MS[attempt]);
        continue;
      }
      throw err;
    }
  }
  // Unreachable given the loop above always returns or throws on the last attempt.
  throw new Error("Could not reach the backend API.");
}

export async function listKnowledgeBaseDocuments(
  onRetry?: (attempt: number, maxAttempts: number) => void
): Promise<{ documents: string[] }> {
  const res = await fetchWithRetry(
    `${API_URL}/api/knowledge-base/documents`,
    { cache: "no-store" },
    onRetry
  );
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

export async function getJobProgress(
  jobId: string,
  onRetry?: (attempt: number, maxAttempts: number) => void
): Promise<JobProgress> {
  const res = await fetchWithRetry(`${API_URL}/api/jobs/${jobId}`, { cache: "no-store" }, onRetry);
  return handle(res);
}

export async function getRequirementDetail(
  jobId: string,
  requirementId: string
): Promise<RequirementResult> {
  const res = await fetchWithRetry(`${API_URL}/api/jobs/${jobId}/requirements/${requirementId}`, {
    cache: "no-store",
  });
  return handle(res);
}

export async function getFinalAnalysis(jobId: string): Promise<FinalAnalysis> {
  const res = await fetchWithRetry(`${API_URL}/api/jobs/${jobId}/final`, { cache: "no-store" });
  return handle(res);
}

export function exportUrl(jobId: string): string {
  return `${API_URL}/api/jobs/${jobId}/export`;
}

export async function getEvalResults(): Promise<EvalResults> {
  const res = await fetchWithRetry(`${API_URL}/api/eval/results`, { cache: "no-store" });
  return handle(res);
}
