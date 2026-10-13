# Antigravity Context Guard & Zero-Token Rules

To prevent accidental token exhaustion and maximize free local execution:

1. **Targeted Reads Only:**
   - NEVER read entire files larger than 150 lines in a single turn.
   - Use `StartLine` and `EndLine` parameters or shell `grep` / `sed`.

2. **Offload Heavy Computation to Local Bash:**
   - Data crunching, JSON parsing, regex replacements MUST be handled via local shell/python scripts ($0.00 cost).
   - Only return the distilled summary or targeted error to the LLM agent.

3. **Subagent Economy:**
   - Launch subagents with concise, self-contained prompts.
   - Do NOT pass large chat history into child workers.

4. **Zero Accidental Third-Party Token Leak:**
   - Keep MCP routing strictly configured to Gemini infra unless explicitly requested.
