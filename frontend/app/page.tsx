"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { createCase, getJob, startAnalysis, uploadArtifact } from "../lib/api";

export default function HomePage() {
  const router = useRouter();
  const [mediaType, setMediaType] = useState<"text" | "video">("text");
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [allegedFile, setAllegedFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string>("Idle");
  const [error, setError] = useState<string>("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!originalFile || !allegedFile) {
      setError("Please upload both original and alleged files.");
      return;
    }

    setError("");
    setBusy(true);

    try {
      setStatus("Creating case");
      const caseResp = await createCase();
      const caseId = caseResp.case_id;

      setStatus("Uploading original artifact");
      await uploadArtifact(caseId, "original", mediaType, originalFile);

      setStatus("Uploading alleged artifact");
      await uploadArtifact(caseId, "alleged", mediaType, allegedFile);

      setStatus("Starting analysis");
      const analyzeResp = await startAnalysis(caseId);

      setStatus("Processing");
      for (;;) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        const job = await getJob(analyzeResp.job_id);
        setStatus(`Job: ${job.stage} (${Math.round(job.progress * 100)}%)`);

        if (job.status === "completed") {
          router.push(`/cases/${caseId}`);
          break;
        }
        if (job.status === "failed") {
          throw new Error(job.error ?? "Analysis failed");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <section className="hero-card">
        <h1>Copycat</h1>
        <p>Deterministic Singapore-first copyright triage and overlap analysis.</p>
        <p className="notice">Triage only. Not legal advice. Uploaded source files auto-delete in 24 hours.</p>
      </section>

      <section className="panel">
        <form onSubmit={onSubmit} className="form-grid">
          <label>
            Media Type
            <select value={mediaType} onChange={(e) => setMediaType(e.target.value as "text" | "video") }>
              <option value="text">Text vs Text</option>
              <option value="video">Video vs Video</option>
            </select>
          </label>

          <label>
            Original Work
            <input
              type="file"
              onChange={(e) => setOriginalFile(e.target.files?.[0] ?? null)}
              accept={mediaType === "text" ? ".txt,.pdf,.docx" : ".mp4,.mov,.mkv,.avi"}
            />
          </label>

          <label>
            Alleged Work
            <input
              type="file"
              onChange={(e) => setAllegedFile(e.target.files?.[0] ?? null)}
              accept={mediaType === "text" ? ".txt,.pdf,.docx" : ".mp4,.mov,.mkv,.avi"}
            />
          </label>

          <button type="submit" disabled={busy}>
            {busy ? "Running..." : "Run Analysis"}
          </button>
        </form>

        <div className="status">{status}</div>
        {error && <div className="error">{error}</div>}
      </section>
    </main>
  );
}