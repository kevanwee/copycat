const API = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");
export type Answer = "yes" | "no" | "unknown";
export type Media = "text" | "image" | "video";
export type Assessment = { answer: Answer; basis: string };
export type Intake = {
  title: string;
  work_category: string;
  claim_route: string;
  conduct_date: string | null;
  assessments: Record<string, Assessment>;
  fair_use_factors: {
    purpose: string;
    nature: string;
    amount: string;
    market: string;
    context: string;
    acknowledgment: string;
    acknowledgment_basis: string;
  };
};
export const emptyIntake: Intake = {
  title: "",
  work_category: "unknown",
  claim_route: "direct",
  conduct_date: null,
  assessments: {},
  fair_use_factors: {
    purpose: "",
    nature: "",
    amount: "",
    market: "",
    context: "other",
    acknowledgment: "unknown",
    acknowledgment_basis: "",
  },
};
export type Citation = { title: string; url: string };
export type Question = {
  id: string;
  phase: string;
  prompt: string;
  explanation: string;
  evidence_needed: string;
  legal_refs: string[];
};
export type Questionnaire = {
  rulepack: {
    questions: Question[];
    citations: Record<string, Citation>;
    reviewed_on: string;
    version: string;
  };
  capabilities: {
    retention_hours: number;
    media: Record<
      Media,
      { available: boolean; max_mb: number; extensions: string[]; note: string }
    >;
  };
};
export type CaseState = {
  case_id: string;
  status: string;
  intake: Intake;
  expires_at: string;
  job_id: string | null;
  artifacts: {
    artifact_id: string;
    role: string;
    media_type: Media;
    filename: string;
    size_bytes: number;
  }[];
};
export type Job = {
  job_id: string;
  status: string;
  stage: string;
  progress: number;
  error: string | null;
};
export type LegalNode = Omit<Question, "id"> & {
  node_id: string;
  answer: Answer;
  basis: string;
  evidence_refs: string[];
};
export type Report = {
  report_id: string;
  case_id: string;
  generated_at: string;
  media_type: Media;
  intake: Intake;
  assessment: {
    status: string;
    title: string;
    summary: string;
    missing_requirements: string[];
    contrary_requirements: string[];
    exception_review: string[];
    scope_notes: string[];
    answered_questions: number;
    total_questions: number;
  };
  headline_overlap_percentage: number;
  component_scores: Record<string, number | null>;
  legal_flow: LegalNode[];
  citations: Record<string, Citation>;
  evidence: {
    method?: string;
    matched_passages?: {
      original_token_start: number;
      alleged_token_start: number;
      length_tokens: number;
      snippet: string;
      snippet_truncated: boolean;
    }[];
    coverage?: { original: number; alleged: number; note: string };
    timeline_matches?: {
      original_timestamp_sec: number;
      alleged_timestamp_sec: number;
      hash_similarity: number;
    }[];
    dimensions?: Record<string, { width: number; height: number }>;
    [key: string]: unknown;
  };
  artifacts: {
    role: string;
    filename: string;
    sha256: string;
    size_bytes: number;
  }[];
  scoring_version: string;
  rule_pack_id: string;
  rule_pack_version: string;
  rule_pack_sha256: string;
  dependencies: Record<string, string>;
  legal_reviewed_on: string;
  source_status: string;
  disclaimers: string[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export function getKey(id: string) {
  return typeof window === "undefined"
    ? ""
    : (sessionStorage.getItem(`copycat:${id}`) ?? "");
}
export function saveKey(id: string, key: string) {
  sessionStorage.setItem(`copycat:${id}`, key);
}
async function request(
  path: string,
  init: RequestInit = {},
  caseId?: string,
): Promise<Response> {
  const headers = new Headers(init.headers);
  if (caseId) headers.set("X-Case-Token", getKey(caseId));
  let res: Response;
  try {
    res = await fetch(`${API}/api/v1${path}`, {
      ...init,
      headers,
      cache: "no-store",
      signal: init.signal ?? AbortSignal.timeout(120_000),
    });
  } catch {
    throw new ApiError(
      "Could not reach the server. Check your connection and retry. Your saved case can be resumed in this tab.",
      0,
    );
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map(
                (d: { loc: string[]; msg: string }) =>
                  `${d.loc.slice(1).join(" · ")}: ${d.msg}`,
              )
              .join("; ")
          : `Request failed (${res.status}). Please retry.`;
    throw new ApiError(message, res.status);
  }
  return res;
}
export async function getQuestionnaire(): Promise<Questionnaire> {
  return (await request("/cases/questionnaire")).json();
}
export async function createCase(intake: Intake) {
  const data = await (
    await request("/cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jurisdiction: "SG", intake }),
    })
  ).json();
  saveKey(data.case_id, data.access_token);
  return data as { case_id: string; access_token: string };
}
export async function updateIntake(id: string, intake: Intake) {
  return request(
    `/cases/${id}/intake`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(intake),
    },
    id,
  );
}
export async function uploadArtifact(
  id: string,
  role: string,
  media: Media,
  file: File,
) {
  const body = new FormData();
  body.set("role", role);
  body.set("media_type", media);
  body.set("file", file);
  return request(`/cases/${id}/artifacts`, { method: "POST", body }, id);
}
export async function startAnalysis(id: string): Promise<{ job_id: string }> {
  return (await request(`/cases/${id}/analyze`, { method: "POST" }, id)).json();
}
export async function getCase(id: string): Promise<CaseState> {
  return (await request(`/cases/${id}`, {}, id)).json();
}
export async function getJob(id: string, caseId: string): Promise<Job> {
  return (await request(`/jobs/${id}`, {}, caseId)).json();
}
export async function getReport(id: string): Promise<Report> {
  return (await (await request(`/cases/${id}/report`, {}, id)).json()).report;
}
export async function deleteCase(id: string) {
  await request(`/cases/${id}`, { method: "DELETE" }, id);
  sessionStorage.removeItem(`copycat:${id}`);
}
export function download(data: Blob, name: string) {
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export async function downloadPdf(id: string) {
  download(
    await (await request(`/cases/${id}/report.pdf`, {}, id)).blob(),
    `copycat-${id}.pdf`,
  );
}
export async function preview(id: string, role: string): Promise<Blob> {
  return (await request(`/cases/${id}/preview/${role}`, {}, id)).blob();
}
