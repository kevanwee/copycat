"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { createCase, getJob, startAnalysis, uploadArtifact } from "../lib/api";

type MediaType = "text" | "video" | "image";

const STEPS = ["Creating case", "Uploading original", "Uploading alleged copy", "Starting analysis", "Processing"];

export default function HomePage() {
  const router = useRouter();
  const [mediaType, setMediaType] = useState<MediaType>("text");
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [allegedFile, setAllegedFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string>("");
  const [error, setError] = useState<string>("");

  const textAccept = ".txt,.pdf,.docx";
  const videoAccept = ".mp4,.mov,.mkv,.avi";
  const imageAccept = ".jpg,.jpeg,.png,.webp,.gif,.bmp,.tiff";
  const accept = mediaType === "text" ? textAccept : mediaType === "image" ? imageAccept : videoAccept;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!originalFile || !allegedFile) {
      setError("Please select both an original and an alleged copy file.");
      return;
    }

    setError("");
    setBusy(true);

    try {
      setStatusMsg(STEPS[0]);
      const caseResp = await createCase();
      const caseId = caseResp.case_id;

      setStatusMsg(STEPS[1]);
      await uploadArtifact(caseId, "original", mediaType, originalFile);

      setStatusMsg(STEPS[2]);
      await uploadArtifact(caseId, "alleged", mediaType, allegedFile);

      setStatusMsg(STEPS[3]);
      const analyzeResp = await startAnalysis(caseId);

      setStatusMsg(STEPS[4]);
      for (;;) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        const job = await getJob(analyzeResp.job_id);
        setStatusMsg(`Processing \u2014 ${job.stage ?? "working"} (${Math.round(job.progress * 100)}%)`);

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
      {/* Hero */}
      <div className="hero">
        <h1>
          <span className="brand">Copycat</span> Copyright Triage
        </h1>
        <p className="sub">
          Deterministic overlap analysis for text and video works under Singapore copyright law.
          Upload both files and receive a scored similarity report in seconds.
        </p>
        <span className="notice">
          ⚠ Triage only &mdash; not legal advice &middot; Files auto-deleted after 24 h &middot; Text, Video &amp; Image comparison
        </span>
      </div>

      {/* Form card */}
      <div className="card">
        <form onSubmit={onSubmit} className="form-grid">

          {/* Media type toggle */}
          <div className="field">
            <span className="field-label">Comparison type</span>
            <div className="type-toggle">
              {(["text", "video", "image"] as MediaType[]).map((t) => (
                <button
                  key={t}
                  type="button"
                  className={`type-option${mediaType === t ? " active" : ""}`}
                  onClick={() => { setMediaType(t); setOriginalFile(null); setAllegedFile(null); }}
                  disabled={busy}
                >
                  {t === "text" ? "📄 Text vs Text" : t === "video" ? "🎬 Video vs Video" : "🎨 Image vs Image"}
                </button>
              ))}
            </div>
          </div>

          {/* Upload zones */}
          <div className="form-row">
            <div className="field">
              <span className="field-label">Original work</span>
              <div className={`upload-zone${originalFile ? " filled" : ""}`}>
                <input
                  key={`orig-${mediaType}`}
                  type="file"
                  accept={accept}
                  onChange={(e) => setOriginalFile(e.target.files?.[0] ?? null)}
                  disabled={busy}
                />
                <span className="upload-icon">{originalFile ? "✅" : "📂"}</span>
                {originalFile
                  ? <span className="upload-filename">{originalFile.name}</span>
                  : <>
                      <span className="upload-text">Click to select original</span>
                      <span className="upload-accept">
                        {mediaType === "text" ? "TXT, PDF, DOCX" : mediaType === "image" ? "JPG, PNG, WEBP, BMP, TIFF" : "MP4, MOV, MKV, AVI"}
                      </span>
                    </>
                }
              </div>
            </div>

            <div className="field">
              <span className="field-label">Alleged copy</span>
              <div className={`upload-zone${allegedFile ? " filled" : ""}`}>
                <input
                  key={`alleged-${mediaType}`}
                  type="file"
                  accept={accept}
                  onChange={(e) => setAllegedFile(e.target.files?.[0] ?? null)}
                  disabled={busy}
                />
                <span className="upload-icon">{allegedFile ? "✅" : "📂"}</span>
                {allegedFile
                  ? <span className="upload-filename">{allegedFile.name}</span>
                  : <>
                      <span className="upload-text">Click to select alleged copy</span>
                      <span className="upload-accept">
                        {mediaType === "text" ? "TXT, PDF, DOCX" : mediaType === "image" ? "JPG, PNG, WEBP, BMP, TIFF" : "MP4, MOV, MKV, AVI"}
                      </span>
                    </>
                }
              </div>
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={busy} style={{ justifySelf: "start" }}>
            {busy ? <><span className="spinner" /> Running analysis…</> : "Run Analysis →"}
          </button>
        </form>

        {busy && statusMsg && (
          <div className="status-strip">
            <span className="spinner" />
            {statusMsg}
          </div>
        )}

        {error && <div className="alert alert-error">{error}</div>}
      </div>

      {/* Info strip */}
      <div className="card-sm" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px" }}>
        {[
          { icon: "🔢", label: "Deterministic", desc: "Same inputs always produce the same score" },
          { icon: "⚖️", label: "SG-First", desc: "Rule pack calibrated to Singapore Copyright Act" },
          { icon: "🎨", label: "3 Media Types", desc: "Text, video, and image comparison supported" },
          { icon: "🔒", label: "No retention", desc: "Source files purged after 24 hours" },
        ].map((f) => (
          <div key={f.label}>
            <div style={{ fontSize: "1.3rem", marginBottom: 4 }}>{f.icon}</div>
            <div style={{ fontWeight: 600, fontSize: "0.875rem" }}>{f.label}</div>
            <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: 2 }}>{f.desc}</div>
          </div>
        ))}
      </div>
    </main>
  );
}
