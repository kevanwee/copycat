"use client";
import { Intake, Questionnaire, Answer } from "../../lib/api";

export function ScopeFields({value, onChange}: {value: Intake; onChange: (v: Intake) => void}) {
  return <div className="field-grid">
    <label className="wide">Comparison name<input maxLength={160} value={value.title} onChange={e => onChange({...value, title: e.target.value})} placeholder="e.g. Article and republished excerpt" /></label>
    <label>Protected work category<select value={value.work_category} onChange={e => onChange({...value, work_category: e.target.value})}>
      <option value="unknown">Not yet established</option><option value="literary">Literary work (including code)</option><option value="dramatic">Dramatic work</option><option value="musical">Musical work</option><option value="artistic">Artistic work (including photograph)</option><option value="film">Film copyright</option><option value="other">Other / multiple rights</option>
    </select><small>A file format does not determine its legal category.</small></label>
    <label>Alleged conduct date<input type="date" value={value.conduct_date ?? ""} onChange={e => onChange({...value, conduct_date: e.target.value || null})}/><small>Leave blank if unknown. Dates affect the applicable law.</small></label>
    <label className="wide">Type of claim<select value={value.claim_route} onChange={e => onChange({...value, claim_route: e.target.value})}><option value="direct">Direct infringement</option><option value="authorisation">Authorising another person’s acts</option><option value="secondary">Importation / commercial dealing</option><option value="unknown">Not yet established</option></select><small>Authorisation and secondary claims are routed for separate legal review.</small></label>
  </div>;
}

export default function IntakeEditor({value, onChange, questionnaire}: {value: Intake; onChange: (v: Intake) => void; questionnaire: Questionnaire}) {
  const phases = [...new Set(questionnaire.rulepack.questions.map(q => q.phase))];
  function setAnswer(id: string, answer: Answer) { onChange({...value, assessments: {...value.assessments, [id]: {answer, basis: value.assessments[id]?.basis ?? ""}}}); }
  function factor(key: string, text: string) { onChange({...value, fair_use_factors: {...value.fair_use_factors, [key]: text}}); }
  return <div className="questionnaire"><div className="notice">Record what the evidence supports. “Unknown” is a valid answer. For yes or no, add a source reference and explanation; the tool does not verify those assertions.</div>
    {phases.map((phase, index) => <details key={phase} open={index === 0} className="question-group"><summary><span className="step-number">{index + 1}</span>{phase}<span className="muted">{questionnaire.rulepack.questions.filter(q => q.phase === phase && value.assessments[q.id]?.answer && value.assessments[q.id].answer !== "unknown").length} / {questionnaire.rulepack.questions.filter(q => q.phase === phase).length} answered</span></summary>
      {questionnaire.rulepack.questions.filter(q => q.phase === phase).map(q => {
        const answer = value.assessments[q.id] ?? {answer: "unknown", basis: ""};
        return <fieldset key={q.id} className="question"><legend>{q.prompt}</legend><p id={`${q.id}-help`} className="muted">{q.explanation}</p>
          <div className="answer-options">{([['unknown', 'Unknown'], ['yes', 'Yes'], ['no', 'No']] as [Answer, string][]).map(([v, label]) => <label key={v} className={answer.answer === v ? "selected" : ""}><input type="radio" name={q.id} value={v} checked={answer.answer === v} onChange={() => setAnswer(q.id, v)} aria-describedby={`${q.id}-help`}/>{label}</label>)}</div>
          <label className="basis-label">Evidence and reasoning {answer.answer !== "unknown" ? "(required)" : "(optional)"}<textarea maxLength={4000} rows={2} value={answer.basis} onChange={e => onChange({...value, assessments: {...value.assessments, [q.id]: {...answer, basis: e.target.value}}})} placeholder={q.evidence_needed}/></label>
          <div className="citations">{q.legal_refs.map(ref => <a key={ref} href={questionnaire.rulepack.citations[ref].url} target="_blank" rel="noreferrer">{questionnaire.rulepack.citations[ref].title} ↗</a>)}</div>
        </fieldset>;
      })}
    </details>)}
    <details className="question-group" open={value.assessments.fair_use?.answer === "yes"}><summary>Fair-use factor worksheet<span className="muted">Sections 191–192</span></summary><div className="question">
      <p>Record each factor and the overall assessment above. The factors are not a numerical test.</p>
      {([['purpose', 'Purpose and character of the use'], ['nature', 'Nature of the source work'], ['amount', 'Amount and importance of the portion used'], ['market', 'Effect on the potential market or value']] as const).map(([key, label]) => <label key={key}>{label}<textarea rows={3} maxLength={4000} value={value.fair_use_factors[key]} onChange={e => factor(key, e.target.value)} /></label>)}
      <label>Use context<select value={value.fair_use_factors.context} onChange={e => factor('context', e.target.value)}><option value="other">Other use</option><option value="news">News reporting</option><option value="criticism_review">Criticism or review</option></select></label>
      {value.fair_use_factors.context !== "other" && <><label>Acknowledgment<select value={value.fair_use_factors.acknowledgment} onChange={e => factor('acknowledgment', e.target.value)}><option value="unknown">Unknown</option><option value="sufficient">Sufficient acknowledgment</option><option value="absent">Absent / insufficient</option>{value.fair_use_factors.context === 'news' && <option value="impossible">Impossible for practical or other reasons</option>}</select></label><label>Acknowledgment evidence<textarea rows={2} maxLength={4000} value={value.fair_use_factors.acknowledgment_basis} onChange={e => factor('acknowledgment_basis', e.target.value)}/></label></>}
    </div></details>
  </div>;
}
