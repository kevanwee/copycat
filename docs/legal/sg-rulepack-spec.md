# SG rulepack v2

`backend/app/rulepacks/sg_v2.json` is the single question/citation catalog used by
the API, UI and legal engine. Each question has a stable ID, phase, plain-language
prompt, explanation, evidence request and citation IDs. The pack specifies ten
core requirements, supported work categories and the reviewed consolidation
period. Source-review limitations are part of the report.

`LegalIntake` validates the supplied context; assessment values are exactly
`yes`, `no` or `unknown`. Known answers require a non-empty basis of at most
4,000 characters. Extra fields and unknown question IDs are rejected. The
work category and claim route are controlled enumerations. Date is a date,
not a freeform string.

## Outcome precedence

1. Unsupported category/route or date outside the reviewed period: `scope_review`.
2. Any core requirement answered no: `not_established`.
3. Independent creation or an exception answered yes: `review_required`.
4. Any core requirement unknown, exception not excluded, or independent-creation
   question unknown: `incomplete`.
5. Otherwise: `supported` on the supplied assessments only.

All missing and contrary core answers and open exceptions remain in the payload
even when another status has precedence. Film assessments carry a separate
underlying-rights scope note. A fair-use yes becomes unknown if any factor note
is missing or the applicable acknowledgment requirement is unresolved. Neither
the engine nor the rulepack reads a similarity score. There is no confidence
percentage, risk probability or automatic fair-use discount.

The v1 rulepack was removed because its defaults and threshold rules were
misleading. Git history retains it for audit. See the
[source-grounded framework](sg-framework-v2.md).
