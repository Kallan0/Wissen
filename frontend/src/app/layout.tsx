import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Wissen Press | Local AI Resume Tailor",
  description: "Tactile editorial papercraft resume builder powered by local ChromaDB vector RAG and local Ollama models.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" type="image/x-icon" href="/wissen-logo.png" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased min-h-screen bg-[#fff8f4] text-[#221a12] font-serif selection:bg-[#c84b31] selection:text-white">
        {children}
      </body>
    </html>
  );
}
