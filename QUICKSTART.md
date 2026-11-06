# Agentic Memory — QuickStart

There are two different things you can do with this project:

1. **Run the memory manager locally.** This is the normal starting point. It is free, private, and does not need ChatGPT, an OpenAI Platform account, an API key, or a tunnel.
2. **Connect ChatGPT to the local memory database.** This is optional and requires a ChatGPT workspace that supports custom MCP servers plus an OpenAI Secure MCP Tunnel.

Start with Part 1. Do not begin with the tunnel.

## Part 1 — Run it locally

### Step 1: Check Python

Python 3.10 or newer is required. Open PowerShell and run:

```powershell
py --version
```

Python 3.13 is suitable. If the command prints a version, continue.

### Step 2: Start the memory manager

Open this repository folder in File Explorer and double-click:

```text
run-memory-manager.cmd
```

A black console window will stay open. That window is the running memory manager. Leave it open while you use the service.

The service is available only on this computer at `http://127.0.0.1:8765`. The console prints a local bearer token. Keep that token private.

### Step 3: Confirm that it is running

Open a second PowerShell window and run:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
```

An `ok` response means the local service is running.

### Step 4: Stop it

When finished, return to the first console window and press **Ctrl+C**. Nothing runs automatically in the background and nothing starts with Windows.

## Part 2 — Optional: connect ChatGPT

Only use this part after Part 1 works. If you only want a local memory manager, stop here.

### What the connection consists of

ChatGPT cannot directly open a private file on your computer. The connection therefore has four pieces:

1. **Your local database** — stays on your computer.
2. **The read-only MCP adapter** — gives ChatGPT limited search and context tools.
3. **The Secure MCP Tunnel** — makes an outbound, authenticated connection from your computer to OpenAI.
4. **The ChatGPT custom MCP connection** — the setting that tells ChatGPT which tunnel to use.

The tunnel is not the memory manager. It is only an optional bridge between ChatGPT and the local read-only adapter.

### Step 1: Install the optional MCP package

Open PowerShell in this repository folder and run:

```powershell
py -m pip install -r requirements-mcp.txt
```

The adapter requires a local startup guard. This is **not** an OpenAI API key and does not create billing:

```powershell
$env:AGENTIC_MEMORY_MCP_TOKEN = 'local-only-startup-guard'
```

Leave this PowerShell window open. The setting applies only to this window.

### Step 2: Check whether ChatGPT supports custom MCP

In ChatGPT, open the settings or connector area and look for an option such as **Add custom MCP server** or **Add connector**.

- If you do not see that option, stop here. Your current plan or workspace does not expose the feature, and the local memory manager still works normally.
- If you do see it, continue.

### Step 3: Create the tunnel in the OpenAI Platform

This is the only step that happens outside this app:

1. Open the [OpenAI Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels).
2. Sign in with the OpenAI account used by the ChatGPT workspace.
3. Choose **Create tunnel** or the equivalent button.
4. Give the tunnel a recognizable name, such as `My local memory`.
5. Follow the page’s setup instructions for the local `tunnel-client`.

**Important download distinction:** the file named `tunnel-client-runtime-cloudflared` is an official OpenAI runtime bundle, but it is intended to run an already-created configuration. For this first setup, download the full **`tunnel-client`** bundle from the Platform page or the [official release page](https://github.com/openai/tunnel-client/releases/latest). The full client is the one that provides the setup, profile, and diagnostic commands. Keep the Cloudflare runtime only if the setup page specifically tells you to use it; do not download `cloudflared` directly from Cloudflare for this guide.

For this Windows computer, choose the **Windows AMD64/x64** download. Do not choose **Windows ARM64**; ARM64 is a different processor architecture.

The Platform page or tunnel client will create a **local tunnel profile** and may ask for a **runtime key**. The runtime key is simply the tunnel client’s password for connecting to that tunnel. It is not the same as an API key.

When prompted, paste the runtime key into the tunnel client’s own credential prompt or local profile setup. Do not paste it into this README, GitHub, ChatGPT messages, a batch file, or a command-line argument. If the page asks you to add API payment details and you do not want API billing, stop without submitting them.

### Step 4: Tell the tunnel what to start

In the tunnel client’s local profile setup, configure the MCP command as follows:

```text
Command: py
Arguments: mcp_server.py stdio
Working folder: this repository folder
```

The profile must also inherit the `AGENTIC_MEMORY_MCP_TOKEN` environment variable from the PowerShell window, or define that same local-only value in the profile’s environment settings.

### Step 5: Start the tunnel

Still in the same PowerShell window, replace the profile name below with the local profile name you created:

```powershell
$env:AGENTIC_MEMORY_TUNNEL_PROFILE = 'YOUR-LOCAL-PROFILE-NAME'
.\run-secure-mcp-tunnel.cmd
```

This command first checks the profile. If the check succeeds, it starts the outbound tunnel. Leave this window open while ChatGPT is using the connection. Press **Ctrl+C** to stop it.

Do not double-click `run-secure-mcp-tunnel.cmd` unless you have already configured `AGENTIC_MEMORY_TUNNEL_PROFILE` as a permanent Windows environment variable. Running it from the same PowerShell window is the clearer and safer option.

### Step 6: Select the tunnel in ChatGPT

Return to ChatGPT and:

1. Open **Add custom MCP server** or **Add connector**.
2. Choose **Tunnel**.
3. Select the tunnel name you created.
4. Review the requested permissions.
5. Connect it.
6. Test the read-only health or search tool first.

If ChatGPT cannot see the tunnel, confirm that the tunnel window is still running and that the selected tunnel name matches the local profile.

## Cost and privacy boundary

The local path in Part 1 does not require a paid service, API key, cloud account, or API billing. Installing this project, installing the MCP package, and running the local service do not create API usage.

ChatGPT subscription billing and API Platform billing are separate. API charges require separately configured API billing and API usage. Do not start the optional broker with `--enable-openai` or add API payment details unless you intentionally want that feature.

The MCP adapter in Part 2 is read-only. It does not write memories, expose arbitrary files, or call the OpenAI API. The tunnel runtime key must remain in the local tunnel client.

## Where local data is stored

The database is created at:

```text
%LOCALAPPDATA%\AgenticMemory\memory.sqlite3
```

For the full design, security notes, API reference, tests, and implementation details, see [README.md](README.md).

