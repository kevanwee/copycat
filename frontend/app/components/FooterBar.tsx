"use client";

import { useState } from "react";

export default function FooterBar() {
  const [open, setOpen] = useState(false);
  const year = new Date().getFullYear();

  return (
    <>
      {/* ── Footer bar ───────────────────────────────────────── */}
      <footer className="site-footer">
        <div className="site-footer-inner">
          <div className="site-footer-left">
            <span className="site-footer-logo">
              <span className="nav-logo-dot" style={{ width: 6, height: 6 }} />
              Copycat
            </span>
            <span className="site-footer-sep" aria-hidden="true">·</span>
            <span>© {year} Copycat. All rights reserved.</span>
            <span className="site-footer-sep" aria-hidden="true">·</span>
            <span>
              Built for Singapore Copyright Act 2021 (No. 22 of 2021) compliance triage.
            </span>
          </div>

          <div className="site-footer-right">
            <a
              href="https://sso.agc.gov.sg/Act/CA2021"
              target="_blank"
              rel="noreferrer"
              className="site-footer-link"
            >
              Singapore Copyright Act
            </a>
            <span className="site-footer-sep" aria-hidden="true">·</span>
            <button
              className="site-footer-link site-footer-link-btn"
              onClick={() => setOpen(true)}
            >
              Terms of Use
            </button>
          </div>
        </div>
      </footer>

      {/* ── Terms-of-Use modal ───────────────────────────────── */}
      {open && (
        <div
          className="tou-backdrop"
          role="dialog"
          aria-modal="true"
          aria-labelledby="tou-title"
          onClick={(e) => { if (e.target === e.currentTarget) setOpen(false); }}
        >
          <div className="tou-modal">
            {/* Header */}
            <div className="tou-header">
              <div>
                <p className="tou-header-sub">Copycat Copyright Triage Platform</p>
                <h2 id="tou-title" className="tou-title">Terms of Use</h2>
              </div>
              <button
                className="tou-close"
                aria-label="Close"
                onClick={() => setOpen(false)}
              >
                ✕
              </button>
            </div>

            {/* Body */}
            <div className="tou-body">
              <p className="tou-effective">
                Effective date: 1 March 2026 &nbsp;|&nbsp; Governing law: Singapore
              </p>

              <p className="tou-intro">
                Please read these Terms of Use (&ldquo;Terms&rdquo;) carefully before using the
                Copycat platform (&ldquo;Platform&rdquo;, &ldquo;Service&rdquo;). By accessing or
                using the Platform, you agree to be bound by these Terms. If you do not agree,
                please do not use the Service.
              </p>

              <TouSection title="1. Nature of the Service">
                <p>
                  Copycat is an automated copyright triage tool that provides a deterministic
                  similarity analysis of uploaded works for informational and preliminary assessment
                  purposes only. The Platform is designed to assist users in understanding potential
                  copyright overlap under the Singapore Copyright Act 2021 (&ldquo;Act&rdquo;).
                </p>
              </TouSection>

              <TouSection title="2. Not Legal Advice">
                <p>
                  <strong>The output of this Platform does not constitute legal advice and must not
                  be relied upon as such.</strong> Copycat is not a law firm, and no
                  solicitor-client relationship is created through your use of the Platform. For
                  legal advice tailored to your circumstances, you should consult a qualified
                  Singapore-licensed legal practitioner.
                </p>
              </TouSection>

              <TouSection title="3. Eligibility and Acceptable Use">
                <p>You agree to use the Platform only for lawful purposes and in accordance with
                these Terms. You must not:</p>
                <ul>
                  <li>Upload content that you do not have the right to submit;</li>
                  <li>Use the Platform to infringe or facilitate infringement of any third-party
                  intellectual property rights;</li>
                  <li>Attempt to reverse-engineer, decompile, or interfere with the Platform;</li>
                  <li>Submit malicious, harmful, or unlawful content;</li>
                  <li>Use automated means to scrape or overload the Platform.</li>
                </ul>
              </TouSection>

              <TouSection title="4. Intellectual Property">
                <p>
                  All software, algorithms, documentation, and design elements of the Platform are
                  owned by or licensed to Copycat and are protected by intellectual property laws.
                  Nothing in these Terms transfers any intellectual property rights to you.
                </p>
                <p>
                  You retain all rights in the content you upload. By uploading content, you grant
                  Copycat a limited, non-exclusive, royalty-free licence to process your files
                  solely for the purpose of delivering the analysis service.
                </p>
              </TouSection>

              <TouSection title="5. Data Retention and Privacy">
                <p>
                  Uploaded files and derived data are automatically purged from our servers within
                  <strong> 24 hours</strong> of upload. We do not store, sell, or share your
                  uploaded content with third parties. Analysis results are stored temporarily
                  to allow you to retrieve your report during the same session.
                </p>
                <p>
                  By using the Platform, you acknowledge and consent to the processing of your
                  files in accordance with this data-handling practice and any applicable
                  Singapore privacy legislation, including the Personal Data Protection Act 2012
                  (&ldquo;PDPA&rdquo;).
                </p>
              </TouSection>

              <TouSection title="6. Accuracy and Limitations">
                <p>
                  Similarity scores produced by the Platform are based on deterministic algorithms
                  and do not account for all legal factors relevant to a copyright claim. Results
                  may not reflect the full legal analysis required to establish or defend against a
                  claim of infringement. Copycat makes no representation that any score threshold
                  corresponds to a legal finding of infringement or non-infringement.
                </p>
              </TouSection>

              <TouSection title="7. Disclaimer of Warranties">
                <p>
                  The Platform is provided &ldquo;as is&rdquo; and &ldquo;as available&rdquo;
                  without warranties of any kind, whether express or implied, including without
                  limitation any implied warranties of merchantability, fitness for a particular
                  purpose, or non-infringement. We do not warrant that the Platform will be
                  uninterrupted, error-free, or free from viruses or other harmful components.
                </p>
              </TouSection>

              <TouSection title="8. Limitation of Liability">
                <p>
                  To the fullest extent permitted by Singapore law, Copycat and its affiliates,
                  officers, employees, agents, and licensors shall not be liable for any indirect,
                  incidental, special, consequential, or punitive damages, including but not
                  limited to loss of profits, data, goodwill, or other intangible losses, arising
                  out of or in connection with your use of the Platform, even if advised of the
                  possibility of such damages.
                </p>
                <p>
                  Our aggregate liability to you for any claims arising from or relating to the
                  Platform shall not exceed S$100 or the amounts paid by you to us in the twelve
                  (12) months preceding the claim, whichever is greater.
                </p>
              </TouSection>

              <TouSection title="9. Third-Party References">
                <p>
                  The Platform may reference third-party legislation, case law, and external
                  resources for informational purposes. We do not endorse and are not responsible
                  for the accuracy or completeness of such third-party content.
                </p>
              </TouSection>

              <TouSection title="10. Modifications to the Service and Terms">
                <p>
                  We reserve the right to modify, suspend, or discontinue the Platform at any
                  time without notice. We may also revise these Terms periodically. Continued use
                  of the Platform after any changes constitutes your acceptance of the updated
                  Terms. The effective date at the top of this document will be updated accordingly.
                </p>
              </TouSection>

              <TouSection title="11. Governing Law and Dispute Resolution">
                <p>
                  These Terms are governed by and construed in accordance with the laws of the
                  Republic of Singapore. Any dispute arising out of or in connection with these
                  Terms, including any question regarding their existence, validity, or
                  termination, shall be submitted to the exclusive jurisdiction of the courts of
                  Singapore.
                </p>
              </TouSection>

              <TouSection title="12. Contact">
                <p>
                  For questions regarding these Terms or the Platform, please contact us via the
                  GitHub repository at{" "}
                  <a
                    href="https://github.com/kevanwee/copycat"
                    target="_blank"
                    rel="noreferrer"
                    className="tou-link"
                  >
                    github.com/kevanwee/copycat
                  </a>
                  .
                </p>
              </TouSection>
            </div>

            {/* Footer */}
            <div className="tou-footer">
              <span>These terms are governed by Singapore law.</span>
              <button className="btn btn-primary" onClick={() => setOpen(false)}>
                I Understand
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function TouSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="tou-section">
      <h3 className="tou-section-title">{title}</h3>
      <div className="tou-section-body">{children}</div>
    </div>
  );
}
