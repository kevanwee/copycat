import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import FooterBar from "./components/FooterBar";

export const metadata: Metadata = {
  title: "Copycat — Copyright Triage",
  description:
    "Singapore-first deterministic copyright overlap analysis and triage tool",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        <nav className="nav" aria-label="Main navigation">
          <Link href="/" className="nav-logo">
            <span className="nav-logo-dot" />
            Copycat
          </Link>
          <div className="nav-right">
            <span className="nav-badge">SG / Evidence workspace</span>
            <a
              href="https://sso.agc.gov.sg/Act/CA2021"
              target="_blank"
              rel="noreferrer"
              className="nav-link"
            >
              Copyright Act
            </a>
          </div>
        </nav>
        {children}
        <FooterBar />
      </body>
    </html>
  );
}
