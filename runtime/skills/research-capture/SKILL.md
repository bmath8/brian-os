---
name: research-capture
description: Use when Brian sends a tweet, X post, thread, link, or any snippet he wants saved as research - "save this", "add to my research", "what's useful here", or just pastes a tweet/URL. Distills it into a structured knowledge-base note for his projects.
---

# Research Capture (X / general)

Turn something Brian pastes into ONE structured note in his knowledge base, so it becomes
searchable and applyable later. Runs on the local model ($0).

## Do
1. Read what Brian pasted (tweet text, thread, link + context). If it's only a bare URL with no
   text and you can't read it, ask him to paste the text (you can't fetch X reliably).
2. Judge value for his projects: AI Job Hunter (income), Boombox, Brian OS Fleet, Job Hunt,
   Learning, or General (stack: React/TS, Next.js, Python, Node, local LLMs/Ollama). If there's
   nothing useful, tell him plainly - don't save filler.
3. Write a note using EXACTLY this template (a real title on the first line):
```
### <short real title>
- **Source:** <@handle (Name) if known> · <date if known> · <url> · <single|thread|reply|quote>
- **Project tags:** [AI Job Hunter | Boombox | Brian OS Fleet | Job Hunt | Learning | General]
- **Topic tags:** #tag #tag
- **Key insight:** <concrete, 1-3 sentences>
- **Why it matters to Brian:** <ties to a project/goal>
- **Actionable takeaway:** <what to DO with it>
- **Apply by:** <a concrete next step, or "reference only">
- **Confidence / freshness:** <high|medium> · <evergreen|time-sensitive>
- **Raw excerpt:** "<key quote>"
```
4. **Append the note** to `C:\Users\mathe\OneDrive\Desktop\Harmony\06_Research\X_Knowledge_Base.md`
   (add a blank line, the note, then `_(saved <today>)_`). Use the file/terminal tool.
5. Reply with the title + project tags + the one-line takeaway so Brian sees what was saved.

## Rules
- One note per item. Be concrete in the takeaway. Never invent the author/date/metrics - leave
  unknown fields blank. The note goes into the RAG-indexed KB, so it'll surface in the brief and
  be queryable ("what did I save about <topic>?").
