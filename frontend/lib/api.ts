const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type CaseResponse = {
  case_id: string;
  jurisdiction: string;
  status: string;
  created_at: string;
};

export type AnalyzeResponse = {
  job_id: string;
  case_id: string;
  status: string;
};

export async function createCase() {
  const res = await fetch(`${API_BASE}/api/v1/cases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jurisdiction: "SG", metadata: {} }),
  });
  if (!res.ok) throw new Error(`Create case failed: ${res.status}`);
  return (await res.json()) as CaseResponse;
}

export async function uploadArtifact(
  caseId: string,
  role: "original" | "alleged",
  mediaType: "text" | "video" | "image",
  file: File,
) {
  const form = new FormData();
  form.set("role", role);
  form.set("media_type", mediaType);
  form.set("file", file);

  const res = await fetch(`${API_BASE}/api/v1/cases/${caseId}/artifacts`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(`Upload failed (${role}): ${message}`);
  }
  return res.json();
}

export async function startAnalysis(caseId: string) {
  const res = await fetch(`${API_BASE}/api/v1/cases/${caseId}/analyze`, { method: "POST" });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(`Analyze failed: ${message}`);
  }
  return (await res.json()) as AnalyzeResponse;
}

export async function getJob(jobId: string) {
  const res = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Job fetch failed: ${res.status}`);
  return res.json();
}

export async function getReport(caseId: string) {
  const res = await fetch(`${API_BASE}/api/v1/cases/${caseId}/report`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Report fetch failed: ${res.status}`);
  return res.json();
}

export function reportPdfUrl(caseId: string): string {
  return `${API_BASE}/api/v1/cases/${caseId}/report.pdf`;
}