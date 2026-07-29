import { defineTool } from "eve/tools";
import { z } from "zod";

// Deterministic ATS helper: compares the job description's salient terms against the
// resume text and returns coverage. The MODEL writes the tailored bullets/cover letter;
// this tool just gives it honest, non-hallucinated keyword facts to work from.
const STOP = new Set([
  "the","and","for","with","you","your","our","are","will","that","this","have","has",
  "from","into","a","an","to","of","in","on","as","is","be","or","we","at","by","it",
  "role","team","work","working","experience","ability","strong","plus","etc",
]);

function terms(text: string): string[] {
  return Array.from(
    new Set(
      (text.toLowerCase().match(/[a-z][a-z0-9+.#-]{2,}/g) ?? []).filter((w) => !STOP.has(w)),
    ),
  );
}

export default defineTool({
  description:
    "Compare a job description against resume text and report ATS keyword coverage: matched terms, missing terms, and a coverage percentage. Helps tailor honestly without inventing experience.",
  inputSchema: z.object({
    jobDescription: z.string().min(1),
    resumeText: z.string().min(1),
  }),
  async execute({ jobDescription, resumeText }) {
    const jd = terms(jobDescription);
    const resume = new Set(terms(resumeText));
    const matched = jd.filter((t) => resume.has(t));
    const missing = jd.filter((t) => !resume.has(t));
    const coveragePct = jd.length ? Math.round((matched.length / jd.length) * 100) : 0;
    return {
      coveragePct,
      matched: matched.slice(0, 40),
      missing: missing.slice(0, 40),
      note: "Address 'missing' terms only where Brian's real background supports them; otherwise flag as a genuine gap.",
    };
  },
});
