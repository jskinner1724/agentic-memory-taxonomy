# Agentic Memory: A Functional Taxonomy

## Overview

Agentic memory is not one thing. It is the set of mechanisms that allow an agent to preserve relevant state, learn from experience, maintain goals, revise beliefs, and act coherently over time.

The familiar categories are:

- **Short-term / working memory** — the active context for the current task.
- **Long-term memory** — information retained across tasks or sessions.
- **Episodic memory** — records of events, interactions, observations, and outcomes.
- **Semantic memory** — general facts, concepts, entities, and relationships.
- **Procedural memory** — knowledge of how to perform actions or workflows.

These are a strong foundation, but they are not fully parallel categories. Working memory describes a time horizon; episodic, semantic, and procedural memory describe different kinds of content that may persist long-term.

## Additional core memory types

### Prospective memory

Memory of intended future actions, reminders, follow-ups, and commitments.

> “After the missing data arrives, update the report and notify the user.”

Without prospective memory, an agent may recall the past accurately while still failing to complete what it promised to do.

### Goal and commitment memory

The objectives, priorities, constraints, obligations, and definitions of success that give a task direction.

Goals should be represented separately from conversation history so that they survive summarization and remain visible during planning.

### Provenance memory

Where a belief came from, who supplied it, what evidence supports it, and whether it was observed, stated, inferred, or guessed.

```text
User stated: “The deadline is Friday.”
Document states: “The deadline is Thursday.”
Agent inference: “There may be a timezone or version conflict.”
```

These should not be stored or weighted as equivalent memories.

### Temporal memory

When something was true, when it changed, when it expires, and what superseded it.

An agent needs to distinguish:

- true now;
- true at a past time;
- expected to become true;
- expired;
- superseded;
- disputed;
- unknown.

### Causal memory

Why something happened, not merely what happened.

```text
Episodic: The deployment failed.
Causal: The deployment failed because production could not access the credential store.
```

Causal memory enables transfer of lessons to new situations.

### Negative or inhibitory memory

Memory of failed approaches, rejected options, forbidden actions, disproven assumptions, safety boundaries, and conditions under which an action should not be attempted.

Expertise consists partly of knowing what to avoid. This is one of the most important and underdeveloped categories in agent systems.

### Social and relational memory

People, roles, relationships, authority, trust, preferences, ownership, and who said or approved what.

This enables an agent to reason about whether a claim came from an owner, reviewer, observer, or untrusted source.

### Identity and self-model memory

The agent’s role, capabilities, limitations, responsibilities, permissions, operating assumptions, and continuity over time.

An agent should remember not only facts about the world, but also facts about what it is allowed and able to do.

### Salience and value memory

Importance, urgency, risk, emotional significance, and expected future usefulness.

This helps determine what deserves retention and attention rather than treating every stored item equally.

### Metamemory

Memory about the reliability and applicability of other memories:

- How confident am I?
- Where did this come from?
- Has it been contradicted?
- When was it last verified?
- Under what conditions should it be retrieved?
- Should I verify it before acting?

Metamemory may be the most important missing category because any persistent memory system will contain errors. A system must represent uncertainty about memory itself.

## A more complete model

Agent memory is better understood as three intersecting dimensions.

### Content

- episodic — what happened;
- semantic — what is believed to be true;
- procedural — how to do something;
- causal — why something happens;
- social — who relates to whom.

### Control

- working — what is active now;
- prospective — what should happen later;
- goal/commitment — what must be achieved;
- inhibitory — what must not happen;
- salience — what deserves attention.

### Epistemic status

- provenance — where it came from;
- confidence — how reliable it is;
- temporal validity — when it applies;
- metamemory — how it should be retrieved or verified.

One memory can occupy several categories at once. For example:

> “Do not use the old migration script because it corrupted production data.”

This is episodic, causal, procedural, inhibitory, provenance-bearing, and confidence-weighted at the same time.

## Recommended architecture

The most promising design is a **predictive, event-sourced memory system**.

```text
experience stream
      ↓
event interpretation
      ↓
belief / goal / procedure updates
      ↓
conflict and time resolution
      ↓
task-specific context reconstruction
      ↓
action
      ↓
observed outcome
```

The system should preserve original evidence separately from its interpretation:

```text
Observation: “The deployment timed out.”
Interpretation: “The connection pool may be exhausted.”
Confidence: 0.55
```

Important memories should be converted into conditional knowledge:

> Method A works under conditions C, fails under conditions D, and should be preferred only when C holds.

When a new task arrives, the agent should reconstruct the smallest context needed for the decision rather than inject all related memories. Retrieval should be based on decision need, authority, temporal validity, causal relevance, and risk—not only semantic similarity.

## Bottom line

The best memory system will not be the one that remembers the most. It will be the one that:

- remembers the right abstractions;
- preserves evidence beneath those abstractions;
- knows when information expires;
- distinguishes facts from interpretations;
- learns from outcomes;
- retrieves according to decisions rather than word similarity;
- revises beliefs without erasing history;
- exposes uncertainty instead of fabricating confidence.

The deepest design principle is:

> A memory should not only answer “what do I remember?” It should also answer “why do I believe it, when is it valid, what follows from it, and what should I avoid because of it?”

## Runnable local prototype

This repository also includes a small local-first memory service that demonstrates these ideas. It uses only the Python standard library and SQLite. It starts no model, contacts no cloud service, and binds only to `127.0.0.1`.

### Requirements and quickstart (Windows)

Python 3.10 or newer is required. On Windows, double-click `run-memory-manager.cmd`. A console window stays open while the service runs; the local bearer token is printed there. Press `Ctrl+C` in that window to stop it. The launcher runs as your normal Windows user and does not install a service or start automatically with Windows.

You can also start it from PowerShell in this folder:

```powershell
python memory_manager.py
```

On first start, the service creates its database in `%LOCALAPPDATA%\AgenticMemory\memory.sqlite3`. It prints a random bearer token once to the terminal. Keep that token private; clients must provide it in the `Authorization: Bearer ...` header. Press `Ctrl+C` to stop the service. No service is installed to run in the background.

The API is intentionally narrow:

- `GET /health` — minimal liveness check; does not expose memory.
- `POST /v1/events` — stores an event and applies deterministic admission rules.
- `POST /v1/memories/candidate` — evaluates and may save a proposed memory.
- `GET /v1/search?q=...` — searches active, unexpired memories.
- `GET /v1/context?task=...` — returns a compact set of matching memories with provenance and confidence.

All routes other than `/health` require the bearer token. Requests are limited to 64 KiB, memory text to 4,000 characters, browser-origin requests are rejected, and request/query contents are omitted from console and audit logs. The API accepts JSON and has no CORS support.

Example (PowerShell; replace the token with the one printed by the running service):

```powershell
$token = 'PASTE-THE-LOCAL-TOKEN-HERE'
$headers = @{ Authorization = "Bearer $token" }
$body = @{ content = 'I prefer concise technical explanations.'; provenance = 'user conversation' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8765/v1/memories/candidate' -Headers $headers -ContentType 'application/json' -Body $body
Invoke-RestMethod -Uri 'http://127.0.0.1:8765/v1/context?task=technical%20explanation' -Headers $headers
```

To choose a database path, pass `--db-path 'C:\path\to\memory.sqlite3'`. To choose a port, use `--port 8765`. By default, the service makes no outbound calls; the optional broker and explicit cloud opt-in are described below. The Windows launcher does not pass `--enable-openai`, so cloud calls stay disabled.

### Admission baseline

The initial admission judge is a transparent heuristic, not a learned classifier. It recognizes a small set of preference, goal, procedure, causal, prospective, and inhibitory phrases, scores candidate durability, and rejects likely one-off statements such as a transient mood. The score and reason codes are returned to the caller. This is a prototype baseline and should not be treated as reliably understanding arbitrary natural language.

Events are retained separately from admitted memories so a rejected event does not become active context. Active memory records include a type, provenance, confidence, status, creation time, optional expiry, and source-event link. Exact duplicate active memories are not added twice. Expired records are excluded from retrieval. The audit table records operation, outcome, and counts/reason codes, but avoids copying query text into the audit log.

### Security and limitations

- Storage stays on the computer; Windows file permissions apply to the database directory. SQLite in this prototype is **not encrypted**. Use Windows device encryption/BitLocker if protection at rest is needed.
- The random API token is printed to the service terminal at startup and exists only for that process. Do not share terminal output or expose this port through a proxy, firewall rule, or network bind.
- Loopback binding and token checks reduce exposure, but this is not a security-audited product. `/health` intentionally reveals only that the local service is responding.
- No dashboard, automatic capture from other applications, model-based memory extraction, automatic consolidation, or MCP transport is included yet. `/v1/events` is the narrow ingestion point for a trusted local connector.
- The service has no automatic background startup and uses one request-handling thread to keep runtime overhead low.

### Local broker and optional OpenAI API

`POST /v1/broker/respond` accepts a JSON object with a `task` string and optional `limit` (maximum eight memories). It retrieves context locally and returns a compact packet containing only the task and selected memory type, text, and confidence. It excludes provenance, source IDs, timestamps, and direct database access. By default it makes no outbound request, even if an API key happens to be present.

The broker applies deterministic redaction to common credentials, bearer tokens, OpenAI/AWS key patterns, email addresses, phone numbers, SSNs, payment-card-like numbers, and values attached to common sensitive field labels such as address or date of birth. It records only redaction categories/counts and outbound metadata in the audit table, never the prompt, API key, or model response. Context sent to the API is capped at approximately 6,000 characters. Redaction is a best-effort filter, not a guarantee or complete data-loss-prevention system; review the data-handling risk before enabling cloud processing.

To enable the optional OpenAI Responses API path, install the official Python SDK and set a key only in the current PowerShell session, then start with the explicit flag:

```powershell
python -m pip install -r requirements-openai.txt
$env:OPENAI_API_KEY = 'YOUR_API_KEY'
python memory_manager.py --enable-openai
```

The key is read from the process environment when a broker request arrives. This application does not write it to disk or include it in database/audit records. The SDK client is created for that request and closed afterward. The outbound request uses the official Python SDK `client.responses.create(...)` method with `store=False`, no tools, and a bounded output. API calls are subject to OpenAI API account billing and data handling; `store=False` does not promise that all provider-side safety or abuse-monitoring retention is disabled. Stop and restart without `--enable-openai` to return to local-only behavior. The default install remains dependency-free.

### Threat model and ChatGPT custom MCP connectivity

The broker is designed to reduce accidental data exposure: local storage remains on the PC; no outbound call occurs by default; a cloud call requires both the startup opt-in flag and `OPENAI_API_KEY`; only a minimized, redacted context packet is sent; and the API key and full prompt are omitted from local audit logs. The service binds to loopback and still requires its bearer token for broker requests.

This does not defend against malware or another process running as your Windows user and reading the process environment, database, or terminal; it does not encrypt SQLite; and deterministic redaction can miss secrets or personal information. The provider receives the minimized prompt whenever the opt-in request is made, and its applicable API data policies still apply. Avoid enabling the cloud path for content that must remain local.

The current loopback API is **not directly connectable to ChatGPT custom MCP**. OpenAI’s setup requires a public HTTPS MCP endpoint, or a supported Secure MCP Tunnel for a private/local server. See [OpenAI’s custom MCP connection guide](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt). ChatGPT custom MCP availability and setup depend on account/workspace support. This repository does not implement MCP transport or configure a tunnel; do not expose the current HTTP service directly to the internet.

### Optional read-only MCP and Secure MCP Tunnel

For direct ChatGPT access without making the memory database public, install the optional MCP dependency:

```powershell
python -m pip install -r requirements-mcp.txt
```

The adapter is intentionally read-only. It exposes only `search_memory`, `get_memory_context`, and `memory_health`; it does not expose memory writes, arbitrary HTTP forwarding, the SQLite file, or the OpenAI API broker. It is designed to run through `tunnel-client` over stdio, so the MCP server remains local and does not need an inbound listener.

OpenAI’s current Secure MCP Tunnel setup is:

1. Sign in to the [OpenAI Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels).
2. Create or select a tunnel endpoint and associate it with the ChatGPT workspace that will use it. Copy the `tunnel_id`.
3. Download the current `tunnel-client` from the tunnel settings page or the [official tunnel-client releases](https://github.com/openai/tunnel-client). Keep it on your PATH.
4. Use `tunnel-client help quickstart` to create a local profile whose MCP command is this repository’s Python executable running `mcp_server.py stdio`.
5. When the client asks for its runtime key, paste it into the client’s local credential/profile setup. Never paste it into this README, a batch file, a command-line argument, a GitHub page, or a chat. If using a PowerShell environment variable, set it only for the current session and clear it when finished.
6. Set the profile name locally, then double-click `run-secure-mcp-tunnel.cmd`. It validates the profile with `tunnel-client doctor` before starting the outbound-only client.
7. In ChatGPT on the web, open Plugins, choose **Add custom MCP server**, select **Tunnel**, select the same tunnel, configure the requested authentication, review the warning, and create the connection. Start with the read-only tools and test `memory_health` first.

The tunnel client needs outbound HTTPS to OpenAI and local access to the MCP command; it does not require an inbound firewall rule. Account, workspace, and tunnel permissions still apply. Do not publish this adapter as a public plugin without a separate security review and production authentication design.

### Tests

Run the standard-library test suite with:

```powershell
python -m unittest discover -s tests -v
```

