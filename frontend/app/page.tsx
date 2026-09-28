"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ApiError,
  analyzeRfp,
  listKnowledgeBaseDocuments,
  uploadKnowledgeBaseDocuments,
} from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<string[] | null>(null);
  const [kbError, setKbError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const [rfpFile, setRfpFile] = useState<File | null>(null);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  const kbInputRef = useRef<HTMLInputElement>(null);

  async function refreshDocuments() {
    try {
      const { documents } = await listKnowledgeBaseDocuments();
      setDocuments(documents);
      setKbError(null);
    } catch (err) {
      setKbError(err instanceof ApiError ? err.message : "Could not reach the backend API.");
    }
  }

  useEffect(() => {
    refreshDocuments();
  }, []);

  async function handleKbUpload(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    setKbError(null);
    try {
      await uploadKnowledgeBaseDocuments(Array.from(files));
      await refreshDocuments();
    } catch (err) {
      setKbError(err instanceof ApiError ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (kbInputRef.current) kbInputRef.current.value = "";
    }
  }

  async function handleAnalyze() {
    if (!rfpFile) return;
    setStarting(true);
    setStartError(null);
    try {
      const { job_id } = await analyzeRfp(rfpFile);
      router.push(`/analysis/${job_id}`);
    } catch (err) {
      setStartError(err instanceof ApiError ? err.message : "Could not start analysis.");
      setStarting(false);
    }
  }

  const kbReady = documents !== null && documents.length > 0;

  return (
    <main className="space-y-8">
      <section>
        <h1 className="text-2xl font-semibold text-gray-900">
          Evidence-backed RFP analysis, end to end
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-gray-600">
          Upload your company&apos;s reference documents, then upload an RFP. A LangGraph
          pipeline extracts requirements, retrieves evidence, assesses capability, drafts a
          response, and validates every claim before handing it to you for review.
        </p>
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">1. Knowledge base</h2>
          {kbReady && (
            <span className="status-pill bg-emerald-100 text-emerald-800">
              {documents!.length} document{documents!.length === 1 ? "" : "s"} indexed
            </span>
          )}
        </div>
        <p className="mt-1 text-sm text-gray-600">
          Seeded automatically with a synthetic demo company knowledge base on first run. Add
          your own reference documents (PDF, DOCX, TXT, MD) to extend it.
        </p>

        {kbError && (
          <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{kbError}</div>
        )}

        {documents && documents.length > 0 && (
          <ul className="mt-4 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
            {documents.map((doc) => (
              <li
                key={doc}
                className="truncate rounded-md bg-gray-50 px-3 py-1.5 text-xs text-gray-700"
              >
                {doc}
              </li>
            ))}
          </ul>
        )}

        <div className="mt-4">
          <label className="inline-flex cursor-pointer items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
            {uploading ? "Uploading..." : "Add reference documents"}
            <input
              ref={kbInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md"
              className="hidden"
              disabled={uploading}
              onChange={(e) => handleKbUpload(e.target.files)}
            />
          </label>
        </div>
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="text-base font-semibold text-gray-900">2. Analyze an RFP</h2>
        <p className="mt-1 text-sm text-gray-600">
          Upload an RFP (PDF, DOCX, TXT, or MD). A sample RFP is included in{" "}
          <code className="rounded bg-gray-100 px-1 py-0.5 text-xs">
            backend/data/sample_rfp/sample_rfp.md
          </code>{" "}
          if you want to try the demo without your own document.
        </p>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="inline-flex cursor-pointer items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
            {rfpFile ? rfpFile.name : "Choose RFP file"}
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md"
              className="hidden"
              onChange={(e) => setRfpFile(e.target.files?.[0] ?? null)}
            />
          </label>

          <button
            onClick={handleAnalyze}
            disabled={!rfpFile || !kbReady || starting}
            className="inline-flex items-center justify-center rounded-md bg-brand-500 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-600 disabled:cursor-not-allowed disabled:bg-gray-300"
          >
            {starting ? "Starting analysis..." : "Start analysis"}
          </button>
        </div>

        {!kbReady && documents !== null && (
          <p className="mt-2 text-xs text-amber-700">
            Knowledge base is empty — add at least one reference document first.
          </p>
        )}
        {startError && (
          <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {startError}
          </div>
        )}
      </section>
    </main>
  );
}
