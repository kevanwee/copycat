"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  CaseState,
  deleteCase,
  download,
  downloadPdf,
  getCase,
  getJob,
  getKey,
  getQuestionnaire,
  getReport,
  Intake,
  Job,
  preview,
  Questionnaire,
  Report,
  saveKey,
  startAnalysis,
  updateIntake,
} from "../../../lib/api";
import IntakeEditor, { ScopeFields } from "../../components/IntakeEditor";

const labels: Record<string, string> = {
  extract: "Reading and validating the files",
  score_text: "Comparing text",
  score_image: "Comparing images",
  score_video: "Aligning video frames",
  legal_triage: "Evaluating the supplied legal assessments",
  report: "Building your report",
  queued: "Waiting for analysis",
  completed: "Complete",
};
const metricNames: Record<string, string> = {
  M1_ngram_jaccard: "Shared word sequences",
  M2_lcs_ratio: "Common token order",
  M3_tfidf_cosine: "Weighted vocabulary",
  M4_entity_overlap: "Named references (regex)",
  I1_phash_similarity: "Perceptual structure",
  I2_color_histogram: "Colour distribution",
  I3_ssim: "Structural similarity",
  I4_orb_feature_match: "Local feature matches",
  V1_frame_phash_alignment: "Aligned frame coverage",
  V2_ssim: "Aligned frame structure",
  V3_psnr_supporting: "Pixel fidelity (supporting)",
  V4_transcript_similarity: "Transcript similarity",
};

function ImageEvidence({ caseId, role }: { caseId: string; role: string }) {
  const [src, setSrc] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    let url = "";
    preview(caseId, role)
      .then((blob) => {
        if (active) {
          url = URL.createObjectURL(blob);
          setSrc(url);
        }
      })
      .catch(() => setError("Preview unavailable. Refer to the source file."));
    return () => {
      active = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [caseId, role]);
  return (
    <figure className="image-evidence">
      {src ? (
        <img
          src={src}
          alt={`${role === "original" ? "Original" : "Comparison"} work, normalized for visual comparison`}
        />
      ) : (
        <p>{error || "Loading preview…"}</p>
      )}
      <figcaption>
        {role === "original" ? "A / Original" : "B / Comparison"} · Normalized
        image
      </figcaption>
    </figure>
  );
}

export default function CasePage() {
  const id = useParams<{ caseId: string }>().caseId;
  const router = useRouter();
  const [state, setState] = useState<CaseState>();
  const [report, setReport] = useState<Report>();
  const [job, setJob] = useState<Job>();
  const [questionnaire, setQuestionnaire] = useState<Questionnaire>();
  const [edit, setEdit] = useState<Intake>();
  const [tab, setTab] = useState("Overview");
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");
  const [needsKey, setNeedsKey] = useState(false);
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState("");
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const load = useCallback(async () => {
    const current = await getCase(id);
    setState(current);
    if (current.status === "completed") {
      setReport(await getReport(id));
      setJob(undefined);
    } else if (current.job_id) {
      setJob(await getJob(current.job_id, id));
    }
    return current;
  }, [id]);
  useEffect(() => {
    if (!getKey(id)) {
      setNeedsKey(true);
      return;
    }
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const start = Date.now();
    async function poll() {
      try {
        const current = await load();
        if (
          active &&
          ["queued", "running", "uploading"].includes(current.status)
        ) {
          if (Date.now() - start < 15 * 60_000) timer = setTimeout(poll, 1500);
          else
            setError(
              "Analysis is taking longer than expected. Check progress again; your case remains saved.",
            );
        }
      } catch (e) {
        if (active) {
          setError((e as Error).message);
          if (e instanceof ApiError && e.status === 404) setNeedsKey(true);
        }
      }
    }
    void poll();
    void getQuestionnaire()
      .then((q) => {
        if (active) setQuestionnaire(q);
      })
      .catch(() => {});
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [id, load, refresh]);
  async function action(name: string, fn: () => Promise<void>) {
    setBusy(name);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function run() {
    await startAnalysis(id);
    setReport(undefined);
    setEdit(undefined);
    setRefresh((v) => v + 1);
  }
  async function saveAndRun() {
    if (!edit) return;
    await updateIntake(id, edit);
    setReport(undefined);
    setState((prev) =>
      prev ? { ...prev, status: "ready", intake: edit } : prev,
    );
    await run();
  }
  const active =
    state && ["queued", "running", "uploading"].includes(state.status);
  const reportTabs = [
    "Overview",
    "Legal analysis",
    "Evidence",
    "Method & sources",
  ];
  return (
    <main id="main" className="workspace">
      <div className="breadcrumb">
        <Link href="/">Comparisons</Link>
        <span>/</span>
        <span>{id.slice(0, 8)}</span>
      </div>
      {needsKey ? (
        <section className="panel access-panel">
          <p className="eyebrow">PRIVATE CASE</p>
          <h1>Open your comparison.</h1>
          <p>
            Enter the access key saved when this case was created. Keys stay in
            this browser tab; the case URL alone does not grant access.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              saveKey(id, key.trim());
              setNeedsKey(false);
              setError("");
              setRefresh((v) => v + 1);
            }}
          >
            <label>
              Case access key
              <input
                type="password"
                autoComplete="off"
                value={key}
                required
                onChange={(e) => setKey(e.target.value)}
              />
            </label>
            <button className="button">Open case</button>
          </form>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
        </section>
      ) : (
        <>
          <header className="report-heading">
            <div>
              <p className="eyebrow">SINGAPORE COPYRIGHT / CASE WORKSPACE</p>
              <h1>{state?.intake.title || "Your comparison"}</h1>
              <p className="muted">
                {state
                  ? `Access expires ${new Date(state.expires_at).toLocaleString()}`
                  : "Opening your case…"}
              </p>
            </div>
            <div className="toolbar">
              {report && (
                <>
                  <button
                    className="button secondary"
                    disabled={Boolean(busy)}
                    onClick={() =>
                      action("Preparing PDF", async () => {
                        await downloadPdf(id);
                      })
                    }
                  >
                    Download PDF ↓
                  </button>
                  <button
                    className="button secondary"
                    onClick={() =>
                      download(
                        new Blob([JSON.stringify(report, null, 2)], {
                          type: "application/json",
                        }),
                        `copycat-${id}.json`,
                      )
                    }
                  >
                    Export JSON
                  </button>
                </>
              )}
            </div>
          </header>
          {error && (
            <div role="alert" className="error">
              {error}
              <button
                className="text-button"
                onClick={() => {
                  setError("");
                  setRefresh((v) => v + 1);
                }}
              >
                Check again
              </button>
            </div>
          )}
          {busy && (
            <p className="loading-line" role="status">
              {busy}…
            </p>
          )}
          {active && (
            <section className="panel progress-panel" aria-live="polite">
              <p className="eyebrow">ANALYSIS IN PROGRESS</p>
              <h2>{labels[job?.stage ?? "queued"] ?? "Processing evidence"}</h2>
              <progress max={1} value={job?.progress ?? 0} />
              <p>You can reload this page to resume checking progress.</p>
            </section>
          )}
          {state && !active && !report && (
            <section className="panel">
              <h2>
                {state.status === "failed"
                  ? "Analysis needs attention"
                  : "Ready to continue"}
              </h2>
              <p>
                {job?.error ||
                  "Review your case details or run the comparison."}
              </p>
              <div className="toolbar">
                <button
                  className="button"
                  disabled={Boolean(busy) || state.artifacts.length !== 2}
                  onClick={() => action("Starting analysis", run)}
                >
                  Run analysis
                </button>
                <button
                  className="button secondary"
                  onClick={() => setEdit(state.intake)}
                >
                  Review context
                </button>
                <Link href="/" className="button secondary">
                  Start with new files
                </Link>
              </div>
            </section>
          )}
          {report && !edit && (
            <>
              <nav className="report-tabs" aria-label="Report sections">
                {reportTabs.map((t) => (
                  <button
                    key={t}
                    aria-pressed={tab === t}
                    onClick={() => setTab(t)}
                  >
                    {t}
                  </button>
                ))}
              </nav>
              {tab === "Overview" && (
                <div className="report-grid">
                  <section className="panel outcome-panel">
                    <p className="eyebrow">LEGAL TRIAGE</p>
                    <span className={`status-pill ${report.assessment.status}`}>
                      {report.assessment.status.replaceAll("_", " ")}
                    </span>
                    <h2>{report.assessment.title}</h2>
                    <p>{report.assessment.summary}</p>
                    <div className="completion">
                      <strong>
                        {report.assessment.answered_questions} /{" "}
                        {report.assessment.total_questions}
                      </strong>
                      <span>questions with a recorded assessment</span>
                    </div>
                    <div className="toolbar">
                      <button
                        className="button"
                        onClick={() => setTab("Legal analysis")}
                      >
                        Inspect legal requirements →
                      </button>
                      <button
                        className="button secondary"
                        disabled={!questionnaire}
                        onClick={() => setEdit(state!.intake)}
                      >
                        Revise context
                      </button>
                    </div>
                  </section>
                  <section className="panel score-panel">
                    <p className="eyebrow">TECHNICAL SIMILARITY</p>
                    <div className="score-number">
                      {report.headline_overlap_percentage.toFixed(1)}
                      <span>/100</span>
                    </div>
                    <p>
                      An algorithmic comparison index. It is not the percentage
                      copied or a probability of infringement.
                    </p>
                    <button
                      className="text-button"
                      onClick={() => setTab("Evidence")}
                    >
                      Inspect the matches →
                    </button>
                  </section>
                  <section className="panel wide">
                    <div className="section-title">
                      <h2>What needs attention</h2>
                      <span className="muted">Next steps</span>
                    </div>
                    {report.assessment.scope_notes.map((n) => (
                      <div key={n} className="attention-item">
                        <span className="dot" />
                        <p>{n}</p>
                      </div>
                    ))}
                    {report.legal_flow
                      .filter(
                        (n) =>
                          n.answer === "unknown" ||
                          report.assessment.contrary_requirements.includes(
                            n.node_id,
                          ) ||
                          ([
                            "fair_use",
                            "other_exception",
                            "independent_creation",
                          ].includes(n.node_id) &&
                            n.answer === "yes"),
                      )
                      .map((n) => (
                        <div key={n.node_id} className="attention-item">
                          <span className={`answer-pill ${n.answer}`}>
                            {n.answer === "unknown" ? "Missing" : "Review"}
                          </span>
                          <div>
                            <strong>{n.prompt}</strong>
                            <p>{n.evidence_needed}</p>
                          </div>
                        </div>
                      ))}
                    {report.assessment.status === "supported" && (
                      <p>
                        Review the underlying evidence and the applicable
                        exceptions with a lawyer before acting. Supplied
                        assessments are not independently verified.
                      </p>
                    )}
                  </section>
                </div>
              )}
              {tab === "Legal analysis" && (
                <section className="panel">
                  <div className="section-title">
                    <div>
                      <p className="eyebrow">REQUIREMENT BY REQUIREMENT</p>
                      <h2>The basis for the assessment.</h2>
                    </div>
                    <button
                      className="button secondary"
                      disabled={!questionnaire}
                      onClick={() => setEdit(state!.intake)}
                    >
                      Revise context
                    </button>
                  </div>
                  <label className="filter">
                    Show
                    <select
                      value={filter}
                      onChange={(e) => setFilter(e.target.value)}
                    >
                      <option value="all">All requirements</option>
                      <option value="unknown">Unknown answers</option>
                      <option value="yes">Yes answers</option>
                      <option value="no">No answers</option>
                    </select>
                  </label>
                  {report.legal_flow
                    .filter((n) => filter === "all" || n.answer === filter)
                    .map((n) => (
                      <article key={n.node_id} className="legal-node">
                        <div className="node-title">
                          <span className={`answer-pill ${n.answer}`}>
                            {n.answer === "unknown"
                              ? "Unknown"
                              : n.answer === "yes"
                                ? "Yes"
                                : "No"}
                          </span>
                          <h3>{n.prompt}</h3>
                        </div>
                        <p>{n.explanation}</p>
                        <div className="recorded-basis">
                          <span className="eyebrow">RECORDED BASIS</span>
                          <p>{n.basis || "No basis supplied."}</p>
                        </div>
                        <p>
                          <strong>Evidence to review:</strong>{" "}
                          {n.evidence_needed}
                        </p>
                        <div className="citations">
                          {n.legal_refs.map((ref) => (
                            <a
                              href={report.citations[ref].url}
                              key={ref}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {report.citations[ref].title} ↗
                            </a>
                          ))}
                        </div>
                      </article>
                    ))}
                  {report.legal_flow.filter(
                    (n) => filter === "all" || n.answer === filter,
                  ).length === 0 && <p>No answers in this category.</p>}
                </section>
              )}
              {tab === "Evidence" && (
                <>
                  <section className="panel">
                    <p className="eyebrow">COMPUTED EVIDENCE</p>
                    <h2>Look at what matches.</h2>
                    <p>{report.evidence.method}</p>
                    <div className="metrics">
                      {Object.entries(report.component_scores).map(
                        ([key, val]) => (
                          <div className="metric" key={key}>
                            <span>{metricNames[key] ?? key}</span>
                            <meter
                              min={0}
                              max={1}
                              value={val ?? 0}
                              aria-label={metricNames[key] ?? key}
                            />
                            <strong>
                              {val === null
                                ? "Not assessed"
                                : `${(val * 100).toFixed(1)}/100`}
                            </strong>
                          </div>
                        ),
                      )}
                    </div>
                  </section>
                  {report.media_type === "image" && (
                    <section className="panel upload-grid">
                      <ImageEvidence caseId={id} role="original" />
                      <ImageEvidence caseId={id} role="alleged" />
                    </section>
                  )}
                  {report.evidence.coverage && (
                    <section className="panel">
                      <h3>Coverage of displayed text matches</h3>
                      <div className="coverage">
                        <span>
                          Original:{" "}
                          <strong>
                            {(report.evidence.coverage.original * 100).toFixed(
                              1,
                            )}
                            %
                          </strong>
                        </span>
                        <span>
                          Comparison:{" "}
                          <strong>
                            {(report.evidence.coverage.alleged * 100).toFixed(
                              1,
                            )}
                            %
                          </strong>
                        </span>
                      </div>
                      <p className="muted">{report.evidence.coverage.note}</p>
                    </section>
                  )}
                  {report.media_type === "text" && (
                    <section className="panel">
                      <h2>Matching text blocks</h2>
                      <p className="muted">
                        Positions are zero-based normalized tokens. Excerpts
                        have case and punctuation normalized; refer to the
                        source for exact quotations.
                      </p>
                      {report.evidence.matched_passages?.length ? (
                        report.evidence.matched_passages.map((p, i) => (
                          <article className="passage" key={i}>
                            <div className="passage-locations">
                              <span>A · token {p.original_token_start}</span>
                              <span>B · token {p.alleged_token_start}</span>
                              <strong>{p.length_tokens} tokens</strong>
                            </div>
                            <p>
                              {p.snippet}
                              {p.snippet_truncated
                                ? " … [excerpt shortened]"
                                : ""}
                            </p>
                          </article>
                        ))
                      ) : (
                        <p>
                          No exact phrase blocks were found. This does not rule
                          out altered copying or a small but important taking.
                        </p>
                      )}
                    </section>
                  )}
                  {report.media_type === "video" && (
                    <section className="panel">
                      <h2>Aligned moments</h2>
                      <p className="muted">
                        Up to 200 matched frames. Audio and underlying rights
                        are not assessed.
                      </p>
                      <div className="table-scroll">
                        <table>
                          <thead>
                            <tr>
                              <th>Original (seconds)</th>
                              <th>Comparison (seconds)</th>
                              <th>Hash similarity</th>
                            </tr>
                          </thead>
                          <tbody>
                            {report.evidence.timeline_matches?.map((m, i) => (
                              <tr key={i}>
                                <td>{m.original_timestamp_sec}</td>
                                <td>{m.alleged_timestamp_sec}</td>
                                <td>
                                  {(m.hash_similarity * 100).toFixed(1)}/100
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {!report.evidence.timeline_matches?.length && (
                        <p>No aligned moments found by this method.</p>
                      )}
                    </section>
                  )}
                </>
              )}
              {tab === "Method & sources" && (
                <section className="panel">
                  <p className="eyebrow">REPRODUCIBILITY & LIMITS</p>
                  <h2>A record you can inspect.</h2>
                  <dl className="review-list">
                    <div>
                      <dt>Scoring version</dt>
                      <dd>{report.scoring_version}</dd>
                    </div>
                    <div>
                      <dt>Legal rules</dt>
                      <dd>
                        {report.rule_pack_id} / {report.rule_pack_version}
                      </dd>
                    </div>
                    <div>
                      <dt>Legal review date</dt>
                      <dd>{report.legal_reviewed_on}</dd>
                    </div>
                    <div>
                      <dt>Report fingerprint</dt>
                      <dd className="mono">{report.report_id}</dd>
                    </div>
                    <div>
                      <dt>Rulepack SHA-256</dt>
                      <dd className="mono">{report.rule_pack_sha256}</dd>
                    </div>
                  </dl>
                  <p className="notice">{report.source_status}</p>
                  <h3>Source files</h3>
                  {report.artifacts.map((a) => (
                    <div className="source-file" key={a.role}>
                      <strong>
                        {a.role}: {a.filename}
                      </strong>
                      <p className="mono">SHA-256 {a.sha256}</p>
                    </div>
                  ))}
                  <h3>Legal sources</h3>
                  <ul className="source-list">
                    {Object.values(report.citations).map((c) => (
                      <li key={c.title}>
                        <a href={c.url} target="_blank" rel="noreferrer">
                          {c.title} ↗
                        </a>
                      </li>
                    ))}
                  </ul>
                  <h3>Limitations</h3>
                  <ul>
                    {report.disclaimers.map((d) => (
                      <li key={d}>{d}</li>
                    ))}
                  </ul>
                  <details>
                    <summary>Dependency versions</summary>
                    <dl className="review-list">
                      {Object.entries(report.dependencies).map(([key, val]) => (
                        <div key={key}>
                          <dt>{key}</dt>
                          <dd>{val}</dd>
                        </div>
                      ))}
                    </dl>
                  </details>
                </section>
              )}
            </>
          )}
          {edit && questionnaire && (
            <section className="panel">
              <h2>Revise the recorded context</h2>
              <p>
                Saving invalidates the previous report and reruns the analysis
                with the same files. Download the previous report first if you
                need its history.
              </p>
              <fieldset disabled={Boolean(busy)} className="form-body">
                <ScopeFields value={edit} onChange={setEdit} />
                <IntakeEditor
                  value={edit}
                  onChange={setEdit}
                  questionnaire={questionnaire}
                />
                <div className="form-actions">
                  <button
                    className="button secondary"
                    onClick={() => setEdit(undefined)}
                  >
                    Cancel
                  </button>
                  <button
                    className="button"
                    onClick={() => action("Saving and rerunning", saveAndRun)}
                  >
                    Save & rerun →
                  </button>
                </div>
              </fieldset>
            </section>
          )}
          {state && (
            <section className="case-controls">
              <details>
                <summary>Case access & deletion</summary>
                <p>
                  Save the access key to reopen this case in another tab. Anyone
                  with the key can read or delete the case.
                </p>
                <div className="toolbar">
                  <button
                    className="button secondary"
                    onClick={() =>
                      download(
                        new Blob(
                          [
                            `Case: ${id}\nURL: ${window.location.origin}/cases/${id}\nAccess key: ${getKey(id)}\nExpires: ${state.expires_at}\n`,
                          ],
                          { type: "text/plain" },
                        ),
                        `copycat-access-${id}.txt`,
                      )
                    }
                  >
                    Save access key
                  </button>
                  <button
                    className="button danger"
                    disabled={Boolean(active || busy)}
                    onClick={() => setDeleteOpen(true)}
                  >
                    Delete case…
                  </button>
                </div>
                {deleteOpen && (
                  <div className="notice">
                    <p>
                      Delete these files, assessments and reports permanently?
                    </p>
                    <div className="toolbar">
                      <button
                        className="button danger"
                        disabled={Boolean(busy)}
                        onClick={() =>
                          action("Deleting case", async () => {
                            await deleteCase(id);
                            router.push("/");
                          })
                        }
                      >
                        Delete permanently
                      </button>
                      <button
                        className="button secondary"
                        onClick={() => setDeleteOpen(false)}
                      >
                        Keep case
                      </button>
                    </div>
                  </div>
                )}
              </details>
            </section>
          )}
        </>
      )}
    </main>
  );
}
