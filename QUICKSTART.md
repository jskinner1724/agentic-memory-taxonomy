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

## Optional: use the read-only MCP server

Skip this section if local-only use is all you need. This connection is optional and is not required for the memory manager to run.

The adapter gives ChatGPT only three read-only tools: search memory, retrieve task context, and check health. It cannot write memories, access arbitrary files, or make API calls.

### A. Install the optional MCP package

From this repository folder, open PowerShell and run:

```powershell
py -m pip install -r requirements-mcp.txt
```

The MCP adapter requires a local startup guard. This is not an OpenAI API key. Set it only for the current PowerShell window:

```powershell
$env:AGENTIC_MEMORY_MCP_TOKEN = 'local-only-mcp-startup-guard'
```

### B. Create the Secure MCP Tunnel

Only do these steps if your ChatGPT plan or workspace supports custom MCP servers:

1. Open the [OpenAI Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels).
2. Create or select a tunnel and copy its tunnel name or ID.
3. Download the current `tunnel-client` from that page or the [official releases](https://github.com/openai/tunnel-client), then make sure `tunnel-client` works from PowerShell.
4. Run `tunnel-client help quickstart` and create a local profile for this repository.
5. Configure the profile to run `py mcp_server.py stdio` from this repository folder.
6. When the tunnel client asks for its runtime key, paste it into the tunnel client’s local credential/profile prompt. Never put it in this repository, a command-line argument, GitHub, or a chat.

### C. Start the tunnel

In the same PowerShell window where you set the startup guard, set the profile name and run the launcher:

```powershell
$env:AGENTIC_MEMORY_TUNNEL_PROFILE = 'YOUR-LOCAL-PROFILE-NAME'
.\run-secure-mcp-tunnel.cmd
```

The launcher validates the profile first and then starts an outbound-only connection. Keep that window open. Press **Ctrl+C** to stop it.

### D. Connect it in ChatGPT

In ChatGPT on the web, open the custom MCP or connector settings, choose **Add custom MCP server**, select **Tunnel**, and select the tunnel you created. The exact menu name can vary by plan and workspace. Review the permissions and start by testing the read-only health tool.

If you do not see custom MCP or Tunnel options, your current plan or workspace may not support them. The local memory manager still works normally without this connection.

## Troubleshooting

- **Python is not recognized:** reinstall Python and enable **Add Python to PATH**, then open a new PowerShell window.
- **The port is already in use:** stop the other local service or start this one with a different port from PowerShell: `python memory_manager.py --port 8766`.
- **The window closes immediately:** start `run-memory-manager.cmd` from PowerShell so any error remains visible.

For the full design, security notes, API reference, tests, and optional integrations, see [README.md](README.md).

