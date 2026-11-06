# Agentic Memory — QuickStart

This is the shortest path to run the local memory manager on Windows.

## Cost and privacy

The local path is free by default. It needs no OpenAI account, API key, tunnel, or cloud connection. The database stays on your PC and the API broker is disabled by default.

API billing is separate from a ChatGPT subscription. Do not add API payment details or start the service with `--enable-openai` unless you intentionally want optional API usage.

## 1. Install Python

Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/windows/). During installation, enable **Add Python to PATH**.

If Python is already installed, open PowerShell and run:

```powershell
python --version
```

## 2. Start the memory manager

In this repository folder, double-click:

```text
run-memory-manager.cmd
```

Keep the console window open. It displays the local bearer token needed by clients. The service listens only on your computer at `127.0.0.1`.

To stop it, click the console window and press **Ctrl+C**.

## 3. Confirm it is running

Open a second PowerShell window and run:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
```

You should see an `ok` response.

## 4. Optional: add a memory manually

Replace the placeholder token with the token printed by the first window:

```powershell
$token = 'PASTE-THE-LOCAL-TOKEN-HERE'
$headers = @{ Authorization = "Bearer $token" }
$body = @{ content = 'I prefer concise technical explanations.'; provenance = 'user conversation' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8765/v1/memories/candidate' -Headers $headers -ContentType 'application/json' -Body $body
```

## Where data is stored

The database is created at:

```text
%LOCALAPPDATA%\AgenticMemory\memory.sqlite3
```

No automatic background service is installed. Nothing starts with Windows unless you choose to launch it.

## Optional: connect ChatGPT

Skip this section if local-only use is all you need.

Direct ChatGPT custom-MCP access depends on your ChatGPT plan and workspace. If you intentionally choose to connect it, use the optional read-only MCP adapter and Secure MCP Tunnel instructions in the main [README](README.md). Keep tunnel credentials in the local tunnel client only—never in this repository, a command line, or a chat.

## Troubleshooting

- **Python is not recognized:** reinstall Python and enable **Add Python to PATH**, then open a new PowerShell window.
- **The port is already in use:** stop the other local service or start this one with a different port from PowerShell: `python memory_manager.py --port 8766`.
- **The window closes immediately:** start `run-memory-manager.cmd` from PowerShell so any error remains visible.

For the full design, security notes, API reference, tests, and optional integrations, see [README.md](README.md).

