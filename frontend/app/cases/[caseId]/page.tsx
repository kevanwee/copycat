"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getReport, reportPdfUrl } from "../../../lib/api";

type PageProps = {
  params: {
    caseId: string;
  };
};

type LegalNode = {
  node_id: string;
  phase: string;
  answer: string;
  confidence: number;
};

type ReportPayload = {
  report_id: string;
  case_id: string;
  jurisdiction: string;
  headline_overlap_percentage: number;
  risk_band: string;
  component_scores: Record<string, number | string>;
  legal_flow: LegalNode[];
  evidence: unknown;
};

const SCORE_LABELS: Record<string, string> = {
  M1_5gram_jaccard: "5-gram Jaccard",
  M2_lcs_ratio: "LCS Ratio",
  M3_tfidf_cosine: "TF-IDF Cosine",
  M4_named_entity_overlap: "Named Entity Overlap",
  V1_frame_phash_alignment: "Frame pHash Alignment",
  V2_ssim: "Structural Similarity (SSIM)",
  V3_psnr_supporting: "PSNR (supporting)",
  V4_transcript_similarity: "Transcript Similarity",
  I1_phash_similarity: "Perceptual Hash",
  I2_color_histogram: "Colour Histogram",
  I3_ssim: "Structural Similarity (SSIM)",
  I4_orb_feature_match: "ORB Feature Match",
};

function getRiskColor(band: string) {
  if (band === "HIGH") return "#dc2626";
  if (band === "MEDIUM") return "#d97706";
  return "#16a34a";
}

function ScoreRing({ pct, band }: { pct: number; band: string }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct / 100);
  const color = getRiskColor(band);

  return (
    <div className="score-panel">
      <div className="score-ring-wrap">
        <svg viewBox="0 0 120 120">
          <circle className="ring-bg" cx="60" cy="60" r={r} />
          <circle
            className="ring-fill"
            cx="60"
            cy="60"
            r={r}
            stroke={color}
            strokeDasharray={circ}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="score-ring-label">
          <span className="score-num" style={{ color }}>{pct.toFixed(1)}</span>
          <span className="score-pct">% overlap</span>
        </div>
      </div>
      <span className={`risk-badge risk-${band}`}>{band} risk</span>
    </div>
  );
}

function ScoreBars({ scores }: { scores: Record<string, number | string> }) {
  const numericEntries = Object.entries(scores).filter(
    ([, v]) => typeof v === "number",
  ) as [string, number][];

  return (
    <div className="score-bars">
      {numericEntries.map(([key, val]) => (
        <div key={key} className="score-bar-row">
          <div className="score-bar-header">
            <span className="score-bar-name">{SCORE_LABELS[key] ?? key}</span>
            <span className="score-bar-val">{(val * 100).toFixed(1)}%</span>
          </div>
          <div className="score-bar-track">
            <div className="score-bar-fill" style={{ width: `${val * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function CaseReportPage({ params }: PageProps) {
  const { caseId } = params;
  const [report, setReport] = useState<ReportPayload | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await getReport(caseId);
        if (!cancelled) {
          setReport(response.report as ReportPayload);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load report");
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [caseId]);

  if (error) {
    return (
      <main className="shell">
        <div className="card">
          <p className="page-title">Report unavailable</p>
          <div className="alert alert-error" style={{ marginTop: 12 }}>{error}</div>
          <div className="actions">
            <Link href="/" className="btn btn-ghost">← Back to triage</Link>
          </div>
        </div>
      </main>
    );
  }

  if (!report) {
    return (
      <main className="shell">
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 12, color: "var(--muted)" }}>
          <span className="spinner" style={{ borderColor: "var(--accent)", borderTopColor: "transparent" }} />
          Loading report…
        </div>
      </main>
    );
  }

  return (
    <main className="shell">
      {/* Header card */}
      <div className="hero">
        <h1><span className="brand">Analysis Report</span></h1>
        <p className="sub">
          Case <code style={{ fontFamily: "JetBrains Mono,monospace", fontSize: "0.85em" }}>{report.case_id}</code>
          &nbsp;&middot;&nbsp;Report <code style={{ fontFamily: "JetBrains Mono,monospace", fontSize: "0.85em" }}>{report.report_id}</code>
          &nbsp;&middot;&nbsp;{report.jurisdiction} jurisdiction
        </p>
        <span className="notice">Non-legal-advice triage output. Deterministic under fixed versions &amp; parameters.</span>
      </div>

      {/* Scores */}
      <div className="card">
        <div className="report-grid">
          {/* Score ring */}
          <ScoreRing pct={report.headline_overlap_percentage} band={report.risk_band} />

          {/* Component bars */}
          <div>
            <p className="section-title">Component scores</p>
            <ScoreBars scores={report.component_scores} />
          </div>
        </div>
      </div>

      {/* Legal flow */}
      <div className="card">
        <p className="section-title">Legal reasoning flow</p>
        <div className="legal-flow">
          {report.legal_flow.map((node) => (
            <div
              key={node.node_id}
              className="legal-node"
              data-answer={node.answer.toLowerCase()}
            >
              <div className="legal-node-left">
                <div className="phase-dot" />
                <span className="phase-tag">{node.phase}</span>
              </div>
              <div className="legal-node-body">
                <div className="legal-node-id">{node.node_id}</div>
                <div className="legal-node-answer">
                  {node.answer === "yes" ? "✓ Yes" : node.answer === "no" ? "✗ No" : node.answer}
                </div>
                <div className="legal-node-conf">confidence {(node.confidence * 100).toFixed(0)}%</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Evidence */}
      <div className="card">
        <p className="section-title">Evidence payload</p>
        <pre className="evidence-pre">{JSON.stringify(report.evidence, null, 2)}</pre>
      </div>

      {/* Actions */}
      <div className="actions">
        <a
          href={reportPdfUrl(caseId)}
          target="_blank"
          rel="noreferrer"
          className="btn btn-primary"
        >
          ↓ Download PDF
        </a>
        <Link href="/" className="btn btn-ghost">← Start new case</Link>
      </div>
    </main>
  );
}