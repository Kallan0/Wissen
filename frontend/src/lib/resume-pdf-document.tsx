import React from "react";
import { Document, Page, StyleSheet, Text, View } from "@react-pdf/renderer";
import { JSONResumeCustomData, ResumeData } from "./types";

const styles = StyleSheet.create({
  page: { padding: 28, color: "#171717", fontFamily: "Times-Roman", fontSize: 9.3, lineHeight: 1.18 },
  header: { textAlign: "center", marginBottom: 8 },
  name: { fontFamily: "Times-Bold", fontSize: 20, lineHeight: 1 },
  label: { color: "#657084", fontSize: 11, marginTop: 3 },
  contact: { fontSize: 8.5, marginTop: 6 },
  section: { marginTop: 7 },
  sectionHeader: { flexDirection: "row", alignItems: "center", marginBottom: 4 },
  rule: { flexGrow: 1, height: 0.7, backgroundColor: "#272727" },
  sectionTitle: { fontFamily: "Times-Bold", fontSize: 11.2, marginHorizontal: 7 },
  summary: { textAlign: "left" },
  entry: { marginBottom: 5 },
  entryLine: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" },
  entryMain: { flexGrow: 1, flexShrink: 1, paddingRight: 8 },
  bold: { fontFamily: "Times-Bold" },
  date: { flexShrink: 0 },
  italic: { fontFamily: "Times-Italic", marginTop: 2 },
  bulletRow: { flexDirection: "row", marginTop: 1.5, paddingLeft: 5 },
  bullet: { width: 8 },
  bulletText: { flex: 1 },
  skillRow: { flexDirection: "row", marginBottom: 2 },
  skillName: { width: 130, fontFamily: "Times-Bold" },
  skillKeywords: { flex: 1 },
  educationDetail: { marginTop: 1 },
});

function displayDate(item: { startDate?: string; endDate?: string; custom?: JSONResumeCustomData }): string {
  const customDate = item.custom?.wissenPress?.displayDate;
  if (customDate) return customDate;
  return [item.startDate, item.endDate].filter(Boolean).join(" - ");
}

function SectionHeading({ children }: { children: string }) {
  return (
    <View style={styles.sectionHeader}>
      <View style={styles.rule} />
      <Text style={styles.sectionTitle}>{children}</Text>
      <View style={styles.rule} />
    </View>
  );
}

function Highlights({ values = [] }: { values?: string[] }) {
  return (
    <>{values.filter(Boolean).map((value, index) => (
      <View style={styles.bulletRow} key={`${value}-${index}`}>
        <Text style={styles.bullet}>•</Text>
        <Text style={styles.bulletText}>{value}</Text>
      </View>
    ))}</>
  );
}

export function ResumePdfDocument({ resume }: { resume: ResumeData }) {
  const basics = resume.basics || {};
  const contact = [
    basics.email,
    basics.phone,
    basics.location?.address,
    ...(basics.profiles || []).map((profile) => profile.url),
    basics.url,
  ].filter(Boolean).join(" | ");

  return (
    <Document title={`${basics.name || "Candidate"} Resume`} author={basics.name || "Candidate"}>
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.name}>{basics.name || "Candidate"}</Text>
          {basics.label ? <Text style={styles.label}>{basics.label}</Text> : null}
          {contact ? <Text style={styles.contact}>{contact}</Text> : null}
        </View>

        {basics.summary ? <View style={styles.section}><SectionHeading>Profile</SectionHeading><Text style={styles.summary}>{basics.summary}</Text></View> : null}

        {(resume.work || []).length ? <View style={styles.section}>
          <SectionHeading>Work Experience & Internships</SectionHeading>
          {(resume.work || []).map((item, index) => <View style={styles.entry} wrap={false} key={`${item.name}-${index}`}>
            <View style={styles.entryLine}>
              <Text style={styles.entryMain}><Text style={styles.bold}>{item.name}</Text>{item.position ? ` - ${item.position}` : ""}{item.location ? ` - ${item.location}` : ""}</Text>
              <Text style={styles.date}>{displayDate(item)}</Text>
            </View>
            <Highlights values={item.highlights} />
          </View>)}
        </View> : null}

        {(resume.projects || []).length ? <View style={styles.section}>
          <SectionHeading>Projects</SectionHeading>
          {(resume.projects || []).map((item, index) => <View style={styles.entry} wrap={false} key={`${item.name}-${index}`}>
            <View style={styles.entryLine}>
              <Text style={[styles.entryMain, styles.bold]}>{item.name}</Text>
              <Text style={styles.date}>{displayDate(item)}</Text>
            </View>
            {(item.keywords || []).length ? <Text style={styles.italic}>{item.keywords?.join(", ")}</Text> : null}
            {item.summary ? <Text>{item.summary}</Text> : null}
            <Highlights values={item.highlights} />
          </View>)}
        </View> : null}

        {(resume.skills || []).length ? <View style={styles.section}>
          <SectionHeading>Skills</SectionHeading>
          {(resume.skills || []).map((item, index) => <View style={styles.skillRow} key={`${item.name}-${index}`}>
            <Text style={styles.skillName}>{item.name}</Text>
            <Text style={styles.skillKeywords}>{(item.keywords || []).join(", ")}</Text>
          </View>)}
        </View> : null}

        {(resume.education || []).length ? <View style={styles.section}>
          <SectionHeading>Education</SectionHeading>
          {(resume.education || []).map((item, index) => <View style={styles.entry} wrap={false} key={`${item.institution}-${index}`}>
            <View style={styles.entryLine}>
              <Text style={styles.entryMain}><Text style={styles.bold}>{item.institution}</Text>{item.custom?.wissenPress?.location ? ` - ${item.custom.wissenPress.location}` : ""}</Text>
              <Text style={styles.date}>{displayDate(item)}</Text>
            </View>
            <Text style={styles.educationDetail}>{[item.studyType, item.area].filter(Boolean).join(" in ")}</Text>
            {item.score ? <Text style={styles.educationDetail}>{item.score}</Text> : null}
          </View>)}
        </View> : null}
      </Page>
    </Document>
  );
}
