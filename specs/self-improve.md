# Self-Improvement Cycle

## Instructions
- Query the brain for recent errors and failures from the last 24 hours
- Identify the top 3 most common failure patterns
- For each pattern, propose a specific edit to the relevant skill file
- Create a git branch for each proposed edit
- Run a test task using the modified skill
- Report results: which edits improved outcomes, which didn't
- Revert unsuccessful edits, keep successful ones for human review
- Store your analysis as a long-term memory in the brain

## Tasks
- [ ] brain_recall recent errors: `brain_recall({ query: "errors failures workarounds", types: ["episodic"] })`
- [ ] Categorize errors by pattern (e.g. OCR failures, focus timing, wrong window, tool timeouts)
- [ ] For each of the top 3 patterns, identify the skill file that could prevent it
- [ ] Create a git branch: `git checkout -b improve/PATTERN_NAME`
- [ ] Edit the skill file with a specific fix (add a step, change timing, add a check)
- [ ] Run a test task that exercises the modified skill
- [ ] Evaluate: did the test task succeed where previous attempts failed?
- [ ] If improved → leave branch for human review. If not → `git checkout main && git branch -D improve/PATTERN_NAME`
- [ ] brain_store a long-term summary: what was tried, what worked, what didn't

## Deliverables
- Git branch(es) with proposed skill edits (if any improvements found)
- Brain long-term memory with cycle analysis
- Summary written to /tmp/self-improve-report.md

## Constraints
- Only edit files in `skills/` and `agents/` — never modify CLI code
- Don't auto-merge. Leave branches for human review.
- If fewer than 3 errors found, work with what's available
- Time limit: 10 minutes. Wrap up and report what you have.
