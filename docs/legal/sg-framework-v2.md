# Singapore copyright triage framework

Research date: 15 September 2026. This note replaces the baseline's numerical
legal-risk model. The scope is civil, direct infringement involving an
identified authorial work or film. It is deliberately longer than a short legal
answer because it specifies the rules and boundaries implemented in software.

## Legal requirements

Under s 146, an act within the copyright must be done in Singapore (or its doing
in Singapore authorised), by someone without ownership or the owner's licence.
Section 39 extends the reference to a work to a substantial part. The claimant
also needs subsisting copyright and standing to sue. Where copying is alleged,
the inquiry includes a causal connection and the taking of protected expression.
Neither substantiality nor fair use is decided by a numerical similarity cutoff.
See [Copyright Act 2021, s 146](https://sso.agc.gov.sg/Act/CA2021?ProvIds=pr146-),
[s 39](https://sso.agc.gov.sg/Act/CA2021?ProvIds=pr39-) and
[Asia Pacific Publishing [2011] SGCA 37, [107]–[113]](https://www.elitigation.sg/gd/s/2011_SGCA_37).

| Limb | Legal requirements and evidence | Implementation |
|---|---|---|
| Identify the work and right | Authorial categories differ from films, recordings, broadcasts and editions; separate copyrights can coexist (ss 8–18, 107). A file format does not identify the legal work. | Explicit category; film-only assessment warns about underlying rights; other categories go to scope review. |
| Subsistence | Authorial works require originality and relevant publication/qualification conditions (ss 109–111); record the identified human author's expression, with recording where required. Film subsistence follows s 123 rather than a generic authorial originality test. | User records category-specific basis; no assumed subsistence. |
| Qualifying connection | Making, first publication, nationality/residence and prescribed international protection can matter (ss 3, 109–111, 123). Singapore citizenship is not a universal requirement. | No inference from selected jurisdiction; foreign-work regulations must be checked for the particular country. |
| Term | Category-specific duration and transition provisions matter (ss 114–116, 125, Part 12). Publication timing and author identification can change the calculation. | Evidence-backed term assessment at conduct date; no universal expiry formula. |
| Standing | Author/maker defaults are subject to employment, commissioning and agreements (ss 133–136); assignment formalities and scope matter (ss 137–142). The owner and, within statutory conditions, an exclusive licensee may sue (ss 153, 156–159). | Chain-of-title and standing assessment; upload ownership is never presumed. |
| Restricted act | Literary/dramatic/musical rights (s 112), artistic rights (s 113), and film rights (s 124) differ. For example, the artistic-work list is not the literary adaptation-right list. | Describe and map the act; technical matching alone cannot satisfy this limb. |
| Territory and permission | Section 146 requires the Singapore nexus and absence of ownership/licence for the alleged actor. | Separate answers for location and permission, including licence scope. |
| Copying | Relevant similarity and access may support an inference, with common source and independent creation considered. Direct evidence can also matter. | Separate causal-connection question and rebuttal question; scores never invent access. |
| Protected expression | Original selection/arrangement can be protected without ownership of underlying facts. Effort verifying facts is not itself the protected expression. | Require identification of the expression relied on and exclusion of mere ideas/facts. |
| Substantial taking | Assess the protected part taken relative to the claimant's work, including qualitative importance (s 39). | Human assessment with pinpoint evidence; no percentage threshold. |
| Exceptions | Section 152 and Part 5 can prevent an otherwise infringing act from infringing. Conditions of the actual provision must be tested. | Fair use and other exceptions remain distinct; unknown is not treated as no exception. |

For the statutory provisions above see the AGC text of
[Part 2](https://sso.agc.gov.sg/Act/CA2021?ProvIds=P12-),
[Part 3](https://sso.agc.gov.sg/Act/CA2021?ProvIds=P13-) and
[Part 5](https://sso.agc.gov.sg/Act/CA2021?ProvIds=P15-).
For originality and the protected part of compilations, see
[Global Yellow Pages [2017] SGCA 28, [24]–[30], [35]–[39]](https://www.elitigation.sg/gd/s/2017_SGCA_28).
These judgments apply the predecessor legislation; the rulepack uses the 2021
Act's current section numbers and treats the judgments as interpretive support.

## Fair use and other permitted uses

Sections 190–191 require consideration of all relevant matters, including the
use's purpose/character, the source work's nature, the portion's extent and
significance, and effects on its market or value. Software records four factor
notes and an overall user assessment; it does not count favourable factors or
automatically discount a score. Section 192 adds acknowledgment conditions:
criticism/review requires sufficient acknowledgment; news reporting allows the
statutory impracticability/impossibility alternative. The latter alternative
must not be imported into criticism/review. See
[ss 190–194](https://sso.agc.gov.sg/Act/CA2021?ProvIds=P15-).

Deemed fair uses under ss 193–194 and other permitted uses require their own
conditions; education, research, computational analysis or nonprofit purpose
alone is not enough. The other-exception answer must identify the provision and
explain satisfaction or failure of its conditions. This is a review register,
not an exhaustive automatic exception engine.

## Routing and judgment boundary

Authorisation and secondary infringement are routed to specialist review.
RecordTV's authorisation discussion addresses control, relationship, precautions
and knowledge in the circumstances; providing a technology does not by itself
resolve liability. The baseline misidentified this case as [2011] SGCA 37, which
is Asia Pacific Publishing. The correct reference is
[RecordTV [2010] SGCA 43, [50]–[60]](https://www.elitigation.sg/gd/s/2010_SGCA_43).
Commercial importation/dealing requires the particular ss 147–150 conditions,
not a direct-copying shortcut. Criminal offences, remedies, moral rights,
limitation, groundless threats, design overlap and disputed international
protection are not determined by this rulepack.

Historical conduct requires the version at that date. The application routes
conduct before the retrieved consolidation's 9 March 2025 effective date to
scope review. In particular, check amendments to
any exception relied on. Never read “not established on supplied assessments”
as a finding of non-infringement or “supported” as a court's verdict.

## Source verification coverage

AGC's downloaded HTML reported **Current version as at 15 Sep 2026**. Its
timeline showed versions effective 9 March 2025 (Act 5 of 2025), 25 November 2024
(Act 32 of 2024), 1 May 2024, 1 November 2022 (Act 31 of 2022), 1 April 2022,
31 December 2021 and 21 November 2021. The 2020 Revised Edition label is not
the date of the current consolidation. The general commencement note places
the relied-on core infringement provisions in the 21 November 2021 tranche;
the retrieved s 193 records a 1 November 2022 amendment. A complete amendment
impact comparison and every foreign-country subsidiary regulation were not
verified, so historical and country-specific conclusions remain for review.

Publisher identity: AGC Legislation Division for statutes; Singapore Courts'
eLitigation service for judgments. Language: English. Publication authority:
official publisher-hosted online consolidations and judgment copies; no
separate Gazette/authentication comparison was performed. Do not describe
these checks as certification of a court-ready citation package.

The regulatory fetch and version scripts succeeded. The base Act URL returned
Part 1, rather than the whole Act: its automatic extraction of four provisions
did **not** cover the legal requirements above. A separate s 146 fetch returned
the operative text, but the extractor with `--pattern numbered` refused its
HTML numbering. No headings were rewritten and no provisions dataset was
handwritten. Relevant Parts 2, 3 and 5 and court texts were subsequently fetched
and read directly. The note paraphrases; it contains no statutory block quotes.
Automated provision/quotation verification is incomplete and is not claimed.
Temporary publisher bytes are not a retained source package.

### Official sources consulted

- [AGC Copyright Act 2021](https://sso.agc.gov.sg/Act/CA2021)
- [AGC s 146](https://sso.agc.gov.sg/Act/CA2021?ProvIds=pr146-)
- [AGC Part 2](https://sso.agc.gov.sg/Act/CA2021?ProvIds=P12-)
- [AGC Part 3](https://sso.agc.gov.sg/Act/CA2021?ProvIds=P13-)
- [AGC Part 5](https://sso.agc.gov.sg/Act/CA2021?ProvIds=P15-)
- [Asia Pacific Publishing [2011] SGCA 37](https://www.elitigation.sg/gd/s/2011_SGCA_37)
- [Global Yellow Pages [2017] SGCA 28](https://www.elitigation.sg/gd/s/2017_SGCA_28)
- [RecordTV [2010] SGCA 43](https://www.elitigation.sg/gd/s/2010_SGCA_43)
- [Flamelite [2009] SGCA 2](https://www.elitigation.sg/gd/s/2009_SGCA_2) was consulted during discovery; not a rulepack dependency.
