"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  createCase,
  emptyIntake,
  getQuestionnaire,
  Intake,
  Media,
  Questionnaire,
  startAnalysis,
  updateIntake,
  uploadArtifact,
} from "../lib/api";
import IntakeEditor, { ScopeFields } from "./components/IntakeEditor";

export default function Home() {
  const router = useRouter();
  const [questionnaire, setQuestionnaire] = useState<Questionnaire>();
  const [intake, setIntake] = useState<Intake>(emptyIntake);
  const [media, setMedia] = useState<Media>("text");
  const [files, setFiles] = useState<{ original?: File; alleged?: File }>({});
  const [step, setStep] = useState(0);
  const [caseId, setCaseId] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [connecting, setConnecting] = useState(true);
  const [recent, setRecent] = useState<string[]>([]);
  async function load() {
    setConnecting(true);
    setError("");
    try {
      setQuestionnaire(await getQuestionnaire());
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setConnecting(false);
    }
  }
  useEffect(() => {
    void load();
    setRecent(
      Object.keys(sessionStorage)
        .filter((k) => k.startsWith("copycat:"))
        .map((k) => k.slice(8))
        .slice(-4),
    );
  }, []);
  function selectFile(role: "original" | "alleged", file?: File) {
    if (!file || !questionnaire) return;
    const cap = questionnaire.capabilities.media[media];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!cap.extensions.includes(ext)) {
      setError(`Choose ${cap.extensions.join(", ")} for ${media}.`);
      return;
    }
    if (!file.size || file.size > cap.max_mb * 1024 * 1024) {
      setError(`Use a non-empty file up to ${cap.max_mb} MB.`);
      return;
    }
    setFiles((prev) => ({ ...prev, [role]: file }));
    setError("");
  }
  function next() {
    if (step === 0 && (!files.original || !files.alleged)) {
      setError("Add both the original and comparison file.");
      return;
    }
    if (
      step === 1 &&
      Object.values(intake.assessments).some(
        (a) => a.answer !== "unknown" && !a.basis.trim(),
      )
    ) {
      setError(
        "Add evidence and reasoning for each yes/no answer, or change it to unknown.",
      );
      return;
    }
    setError("");
    setStep(step + 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  async function submit() {
    if (!files.original || !files.alleged) return;
    setError("");
    try {
      setBusy("Saving the comparison");
      let id = caseId;
      const data = {
        ...intake,
        title: intake.title.trim() || "Untitled comparison",
      };
      if (!id) {
        id = (await createCase(data)).case_id;
        setCaseId(id);
      } else {
        await updateIntake(id, data);
      }
      setBusy("Uploading the original file");
      await uploadArtifact(id, "original", media, files.original);
      setBusy("Uploading the comparison file");
      await uploadArtifact(id, "alleged", media, files.alleged);
      setBusy("Starting analysis");
      await startAnalysis(id);
      router.push(`/cases/${id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy("");
    }
  }
  const answered = Object.values(intake.assessments).filter(
    (a) => a.answer !== "unknown",
  ).length;
  return (
    <main id="main" className="workspace">
      <section className="intro">
        <p className="eyebrow">SINGAPORE COPYRIGHT · EVIDENCE TRIAGE</p>
        <h1>Start with the evidence.</h1>
        <p className="lead">
          Compare two works, examine the legal requirements, and build a clear
          record of what still needs review.
        </p>
      </section>
      <div className="workspace-grid">
        <section className="panel intake-panel">
          <ol className="stepper" aria-label="Comparison steps">
            {["Files & scope", "Legal context", "Review & run"].map(
              (label, i) => (
                <li
                  key={label}
                  aria-current={step === i ? "step" : undefined}
                  className={step === i ? "active" : ""}
                >
                  <span>{i + 1}</span>
                  {label}
                </li>
              ),
            )}
          </ol>
          {error && (
            <div role="alert" className="error">
              {error}
              {!questionnaire && (
                <button
                  className="text-button"
                  onClick={load}
                  disabled={connecting}
                >
                  Retry connection
                </button>
              )}
            </div>
          )}
          {!questionnaire ? (
            <p role="status">
              {connecting
                ? "Connecting to the analysis service…"
                : "The analysis service is unavailable. Retry the connection to continue."}
            </p>
          ) : (
            <fieldset disabled={Boolean(busy)} className="form-body">
              {step === 0 && (
                <>
                  <div className="section-heading">
                    <p className="eyebrow">01 / FILES & SCOPE</p>
                    <h2>What are you comparing?</h2>
                    <p>
                      Use the claimant’s work as the original and the alleged
                      copy as the comparison.
                    </p>
                  </div>
                  <div
                    className="media-options"
                    role="group"
                    aria-label="Media type"
                  >
                    {(["text", "image", "video"] as Media[]).map((m) => (
                      <button
                        type="button"
                        key={m}
                        aria-pressed={media === m}
                        disabled={
                          !questionnaire.capabilities.media[m].available
                        }
                        onClick={() => {
                          setMedia(m);
                          setFiles({});
                          setError("");
                        }}
                      >
                        <span className="media-icon">
                          {m === "text" ? "Aa" : m === "image" ? "▧" : "▷"}
                        </span>
                        <strong>
                          {m === "text"
                            ? "Documents"
                            : m === "image"
                              ? "Images"
                              : "Video"}
                        </strong>
                        {!questionnaire.capabilities.media[m].available && (
                          <small>Unavailable on this server</small>
                        )}
                      </button>
                    ))}
                  </div>
                  <p className="hint">
                    {questionnaire.capabilities.media[media].note}
                  </p>
                  <div className="upload-grid">
                    {(["original", "alleged"] as const).map((role) => (
                      <label
                        key={role}
                        className={`upload-zone ${files[role] ? "has-file" : ""}`}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={(e) => {
                          e.preventDefault();
                          selectFile(role, e.dataTransfer.files[0]);
                        }}
                      >
                        <span className="eyebrow">
                          {role === "original"
                            ? "A / ORIGINAL WORK"
                            : "B / COMPARISON WORK"}
                        </span>
                        <strong>
                          {files[role]?.name || "Choose a file or drop it here"}
                        </strong>
                        <span>
                          {files[role]
                            ? `${(files[role]!.size / 1024).toFixed(1)} KB · Click to replace`
                            : `${questionnaire.capabilities.media[media].extensions.join(" · ")} · ${questionnaire.capabilities.media[media].max_mb} MB max`}
                        </span>
                        <input
                          aria-label={
                            role === "original"
                              ? "Original file"
                              : "Comparison file"
                          }
                          type="file"
                          accept={questionnaire.capabilities.media[
                            media
                          ].extensions.join(",")}
                          onChange={(e) =>
                            selectFile(role, e.target.files?.[0])
                          }
                        />
                      </label>
                    ))}
                  </div>
                  <ScopeFields value={intake} onChange={setIntake} />
                </>
              )}
              {step === 1 && (
                <>
                  <div className="section-heading">
                    <p className="eyebrow">02 / LEGAL CONTEXT</p>
                    <h2>What does the evidence establish?</h2>
                    <p>
                      You can run an initial comparison with unknown answers,
                      then revise the assessment after inspecting the matches.
                    </p>
                  </div>
                  <IntakeEditor
                    value={intake}
                    onChange={setIntake}
                    questionnaire={questionnaire}
                  />
                </>
              )}
              {step === 2 && (
                <>
                  <div className="section-heading">
                    <p className="eyebrow">03 / REVIEW & RUN</p>
                    <h2>Ready for a first assessment.</h2>
                    <p>
                      Check the inputs. Your report will distinguish technical
                      matches from supplied legal assessments.
                    </p>
                  </div>
                  <dl className="review-list">
                    <div>
                      <dt>Comparison</dt>
                      <dd>{intake.title || "Untitled comparison"}</dd>
                    </div>
                    <div>
                      <dt>Original</dt>
                      <dd>{files.original?.name}</dd>
                    </div>
                    <div>
                      <dt>Comparison file</dt>
                      <dd>{files.alleged?.name}</dd>
                    </div>
                    <div>
                      <dt>Category / route</dt>
                      <dd>
                        {intake.work_category} / {intake.claim_route}
                      </dd>
                    </div>
                    <div>
                      <dt>Conduct date</dt>
                      <dd>
                        {intake.conduct_date || "Unknown — scope review needed"}
                      </dd>
                    </div>
                    <div>
                      <dt>Legal questions</dt>
                      <dd>
                        {answered} answered ·{" "}
                        {questionnaire.rulepack.questions.length - answered}{" "}
                        unknown
                      </dd>
                    </div>
                  </dl>
                  <div className="notice">
                    <strong>Before uploading</strong>
                    <p>
                      Use files you are authorised to submit. Files and report
                      contents are sent to the configured analysis server. Cases
                      expire after {questionnaire.capabilities.retention_hours}{" "}
                      hours; active-service cleanup removes the stored material.
                      Download your report before expiry.
                    </p>
                  </div>
                </>
              )}
              <div className="form-actions">
                {step > 0 && (
                  <button
                    className="button secondary"
                    onClick={() => setStep(step - 1)}
                  >
                    Back
                  </button>
                )}
                <span className="muted">
                  {busy ||
                    (step === 1
                      ? `${answered} of ${questionnaire.rulepack.questions.length} questions answered`
                      : "Unknown facts stay unknown")}
                </span>
                {step < 2 ? (
                  <button className="button" onClick={next}>
                    Continue →
                  </button>
                ) : (
                  <button className="button" onClick={submit}>
                    Run comparison →
                  </button>
                )}
              </div>
            </fieldset>
          )}
          {busy && (
            <p role="status" className="loading-line">
              {busy}…
            </p>
          )}
        </section>
        <aside className="sidebar">
          <section className="side-card">
            <span className="mini-symbol">A ↔ B</span>
            <h2>A useful first view.</h2>
            <p>Three parts, one reviewable record.</p>
            <ol className="benefits">
              <li>
                <strong>Compare the works</strong>
                <span>
                  Repeatable text and visual metrics with identifiable matches.
                </span>
              </li>
              <li>
                <strong>Check each legal limb</strong>
                <span>
                  Protection, rights, copying, substantial taking and
                  exceptions.
                </span>
              </li>
              <li>
                <strong>Know the next step</strong>
                <span>
                  See missing evidence and export a source-linked report.
                </span>
              </li>
            </ol>
          </section>
          <div className="side-note">
            <strong>Similarity is not infringement.</strong>
            <p>
              A short but important taking may matter. Shared facts or ideas may
              not. The legal assessment needs context and human judgment.
            </p>
          </div>
          {recent.length > 0 && (
            <section className="side-note">
              <h3>Resume in this tab</h3>
              {recent.map((id) => (
                <Link key={id} className="recent-link" href={`/cases/${id}`}>
                  Comparison {id.slice(0, 8)} ↗
                </Link>
              ))}
            </section>
          )}
        </aside>
      </div>
    </main>
  );
}
