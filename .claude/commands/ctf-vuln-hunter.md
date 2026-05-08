---
name: ctf-vuln-hunter
description: >
  Run Claude Code CLI as an autonomous vulnerability scanner on a target source file or directory.
  Use this skill whenever the user wants to scan code for security vulnerabilities, find bugs in C/C++
  or other source files, run a CTF-style analysis, audit code for exploits, or wants Claude to
  explain a vulnerability, replicate it, and propose a fix. Triggers on phrases like "find vulnerabilities",
  "scan for bugs", "audit this code", "CTF", "security scan", "exploit analysis", or any request
  to analyze source code for security issues and produce a structured report.
---

# CTF Vulnerability Hunter

Autonomous security scanner that uses the Claude Code CLI (`claude`) to analyze source code,
identify the most critical vulnerability, explain it, show how to replicate it, and propose a fix.

---

## Workflow

### 1. Gather inputs

Ask the user (if not already provided):
- **Source path** – file or directory to scan (e.g. `/src/foo.c`, `./project/`)
- **Output path** – where to write the report (default: `/tmp/vuln_report.txt`)
- **Log path** – where to stream Claude Code output (default: `/tmp/claude_vuln.log`)

If the user supplies a file upload or pastes code inline, save it to `/tmp/target_src/` first.

### 2. Build the Claude Code CLI command

Compose the command using the template below, substituting the actual paths:

```bash
claude \
  --dangerously-skip-permissions \
  -p "You are a senior security researcher participating in a CTF challenge.

Your mission:
1. Read and analyze the source code at: <SOURCE_PATH>
2. Identify ALL potential vulnerabilities (buffer overflows, format string bugs, use-after-free,
   integer overflows, injection flaws, race conditions, insecure crypto, etc.)
3. Select the MOST CRITICAL vulnerability found.
4. Produce a structured security report written to <OUTPUT_PATH> with EXACTLY this format:

---
VULNERABILITY REPORT
====================

## Vulnerability
[Name and CWE ID if applicable]

## Location
[File, function name, line number(s)]

## Description
[Clear technical explanation of the flaw and why it is dangerous]

## How to Replicate
[Step-by-step instructions or a minimal PoC payload/exploit to trigger the vulnerability]

## Proposed Fix
[Corrected code snippet or patch, with explanation of why the fix works]

## Severity
[CRITICAL / HIGH / MEDIUM / LOW — with brief justification]
---

If NO vulnerability is found, write 'NO VULNERABILITIES DETECTED' to the report file.
" \
  --verbose \
  &> <LOG_PATH>
```

### 3. Run the command

Execute the command in a bash subshell. Stream output to the log path.

```bash
# Example execution
claude \
  --dangerously-skip-permissions \
  -p "..." \
  --verbose \
  &> /tmp/claude_vuln.log
```

Monitor the log while it runs and show the user progress if it takes more than a few seconds.

### 4. Read and present the report

After the command exits:

1. Check if the output file exists and is non-empty.
2. If yes — read it and display the full report to the user in a formatted block.
3. If no — read the log file and summarize what happened (error, no file found, etc.).

```bash
cat <OUTPUT_PATH>
```

### 5. Follow-up

Offer the user:
- Run a deeper scan on additional files
- Export the report as a `.md` or `.txt` file via `present_files`
- Scaffold a patch/fix file from the proposed fix section

---

## Error handling

| Situation | Action |
|---|---|
| `claude` CLI not found | Tell user to install Claude Code: `npm install -g @anthropic-ai/claude-code` |
| Source file not found | Ask user to confirm path or re-upload the file |
| Report file empty | Read the log and report the failure reason |
| Non-zero exit code | Surface the last 20 lines of the log to the user |

---

## Security note

`--dangerously-skip-permissions` is required for the CLI to read files and write the report
without interactive prompts. Only use this on isolated/sandboxed environments or files you own.
Always inform the user of this flag and its implications before running.

---

## Example invocation (C file)

```bash
claude \
  --dangerously-skip-permissions \
  -p "You are a senior security researcher...
      Source: /src/foo.c
      Report output: /out/report.txt" \
  --verbose \
  &> /tmp/claude.log
```
