"use client";

import { PDFViewer } from "@react-pdf/renderer";
import { ResumePdfDocument } from "@/lib/resume-pdf-document";
import { ResumeData } from "@/lib/types";

export default function ResumePdfViewer({ resume }: { resume: ResumeData }) {
  return (
    <PDFViewer className="block min-h-[1120px] w-full border-0 bg-white" showToolbar={false}>
      <ResumePdfDocument resume={resume} />
    </PDFViewer>
  );
}
