---
name: code-review
description: >
  Reviews code for correctness, security, performance, maintainability, and best practices.
  Use when a user asks for a code review, to check a pull request, or to analyze a snippet
  for potential issues. Provides actionable, constructive feedback with prioritised
  suggestions. Integrates with linters and formatters if available.
license: MIT
compatibility: No special environment required; optional integration with local linters.
allowed-tools: Read, Bash(pylint:*), Bash(eslint:*), Bash(rubocop:*)
metadata:
  author: agent-skill-collective
  version: "1.0"
---

# Code Review Skill

## Overview
This skill performs thorough, human-like code reviews. It prioritises finding
real bugs and design issues over stylistic nitpicking, unless a project-specific
style guide is provided. Feedback is structured, constructive, and actionable.

## Workflow
Follow this sequence every time. Never skip steps.

1. **Understand the context**
   - What is the code supposed to do? (ask if unclear)
   - Which language, framework, and testing practices are in use?
   - Is this a full file, a diff, or a standalone snippet?

2. **Run automated checks (if possible)**
   - If a linter or formatter is available (e.g., `pylint`, `eslint`, `rubocop`), run it first.
   - Summarise any machine-detectable issues under "Automated findings" in the output.
   - Do not repeat every linting detail; link to the full output or attach it.

3. **Perform a structured manual review**
   Go through the following dimensions in order. For each, flag issues as
   **High**, **Medium**, or **Low** severity.

   - **Correctness**: logic errors, off-by-one, mishandled edge cases, race conditions
   - **Security**: injection risks (SQL, OS command, XSS), hardcoded secrets, improper authz/authn
   - **Performance**: N+1 queries, unnecessary loops, memory leaks, blocking I/O
   - **Maintainability**: confusing naming, deeply nested logic, God objects, missing tests
   - **Style & readability**: only flag issues that genuinely harm readability (e.g., inconsistent naming within the same small scope, missing comments where the intent is non-obvious)

4. **Look for hidden assumptions**
   - Does the code assume a specific environment, locale, or timezone?
   - Are there any silent failures (e.g., swallowed exceptions)?

5. **Suggest specific improvements**
   - **Never** just say “this is bad”. Explain *why* and provide a concrete fix.
   - When possible, offer code examples for the suggested change.
   - If a suggestion might alter behaviour, clearly state the trade-off.

6. **Format the final review**
   Use the output template below. Be respectful and focus on the code, not the author.

## Output Template
Always structure your response like this:

```
## Code Review Summary
[2-3 sentences on overall quality and the most important takeaway]

### High Priority
- [Issue description, location, why it matters, suggested fix]
- ...

### Medium Priority
- ...

### Low Priority / Nitpicks
- ...

### Automated Findings
- [Linter results or “none”]

### Questions
- [Anything you need clarified, or open suggestions for the author]
```

## Guidelines for Effective Reviews

- **Be constructive**: Frame suggestions as improvements, not criticism.
  - Good: “Renaming this variable to `userCount` would make its purpose clearer.”
  - Avoid: “This variable name is terrible.”

- **Be specific**: Always reference file name, line number, or function name when available.

- **Don’t fix what isn’t broken**: If the code works correctly and follows project conventions, leave it alone.

- **Respect the author’s time**: If you suggest a cosmetic change, note whether it’s worth doing now or could wait.

- **Adapt to the language**: Apply idioms and best practices of the specific language (e.g., list comprehensions in Python, RAII in C++).

- **Encourage testing**: If the change lacks tests, suggest adding them, especially for critical logic.

## Common Edge Cases

- **No code provided**: ask the user to paste the code or specify the file(s).
- **Large multi-file review**: review one file at a time, and offer a summary at the end.
- **Partial diff**: note that you can only review what you see; ask if surrounding context matters.
- **Conflicting style guides**: if the user provides a style guide (e.g., PEP 8, Airbnb JS), follow it strictly over general advice.

## Progressive Disclosure
This file covers the core workflow. When you need:
- A comprehensive checklist of common security pitfalls → read `references/security_checklist.md`
- A systematic guide to detecting logical errors and internal contradictions → read `references/logical_error_detection.md`
- Language-specific best practices (e.g., Python, JavaScript, Go) → read the appropriate file in `references/language_guides/`
- Instructions on integrating linters not auto-detected → see `scripts/run_linters.sh` comments

Remember: only load `references/` when you are about to review a piece of code that matches a specific risk or language.
