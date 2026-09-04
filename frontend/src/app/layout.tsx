import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Local AI Resume Builder | Privacy-First Career Tailor",
  description: "Privacy-first, retrieval-augmented generation (RAG) system tailoring resumes to job descriptions using local LLMs and ChromaDB.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}
