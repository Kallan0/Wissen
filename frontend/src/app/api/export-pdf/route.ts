import React from "react";
import { renderToBuffer } from "@react-pdf/renderer";
import { validate } from "@jsonresume/schema";
import { ResumePdfDocument } from "@/lib/resume-pdf-document";
import { ResumeData } from "@/lib/types";

export const runtime = "nodejs";

function validateResume(resume: ResumeData): Promise<void> {
  return new Promise((resolve, reject) => {
    validate(resume, (errors: unknown, valid: boolean) => {
      if (valid) resolve();
      else reject(new Error(`Invalid JSON Resume: ${JSON.stringify(errors)}`));
    });
  });
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const resume = body?.resume_data as ResumeData;
    if (!resume || typeof resume !== "object") {
      return Response.json({ error: "resume_data is required" }, { status: 400 });
    }
    await validateResume(resume);
    const document = React.createElement(ResumePdfDocument, { resume }) as unknown as Parameters<typeof renderToBuffer>[0];
    const pdf = await renderToBuffer(document);
    return new Response(new Uint8Array(pdf), {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": "attachment; filename=resume.pdf",
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "PDF generation failed";
    return Response.json({ error: message }, { status: 400 });
  }
}
