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
        <section className="panel">
          <h1>Report Unavailable</h1>
          <p className="error">{error}</p>
          <Link href="/">Back</Link>
        </section>
      </main>
    );
  }

  if (!report) {
    return (
      <main className="shell">
        <section className="panel">
          <h1>Loading report...</h1>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <section className="hero-card">
        <h1>Case Report {report.report_id}</h1>
        <p>
          Case: {report.case_id} | Jurisdiction: {report.jurisdiction}
        </p>
        <p className="notice">Non-legal-advice triage output.</p>
      </section>

      <section className="panel">
        <div className="metric">
          <h2>Headline Overlap</h2>
          <p className="big">{report.headline_overlap_percentage}%</p>
          <p>
            Risk band: <strong>{report.risk_band}</strong>
          </p>
        </div>

        <h3>Component Scores</h3>
        <ul className="list">
          {Object.entries(report.component_scores).map(([k, v]) => (
            <li key={k}>
              {k}: {String(v)}
            </li>
          ))}
        </ul>

        <h3>Legal Flow</h3>
        <ul className="list">
          {report.legal_flow.map((node) => (
            <li key={node.node_id}>
              [{node.phase}] {node.node_id} {"->"} <strong>{node.answer}</strong> (confidence {node.confidence})
            </li>
          ))}
        </ul>

        <h3>Evidence</h3>
        <pre className="code">{JSON.stringify(report.evidence, null, 2)}</pre>

        <div className="actions">
          <a href={reportPdfUrl(caseId)} target="_blank" rel="noreferrer">
            Download PDF
          </a>
          <Link href="/">Start New Case</Link>
        </div>
      </section>
    </main>
  );
}