$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Stop-WithMessage([string]$message) {
    Write-Host ""
    Write-Host $message -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "Agentic Memory - Connect ChatGPT" -ForegroundColor Cyan
Write-Host ""
Write-Host "This guided setup will:" 
Write-Host "  1. Find the full Windows AMD64 tunnel client"
Write-Host "  2. Create or check a local tunnel profile"
Write-Host "  3. Start the read-only MCP connection"
Write-Host ""
Write-Host "Your runtime key is entered privately and is not saved in this repository."
Write-Host ""

$clientPath = $null
$defaultClient = Join-Path $projectRoot "tunnel-client.exe"
if (Test-Path $defaultClient) {
    $clientPath = $defaultClient
} else {
    Add-Type -AssemblyName System.Windows.Forms
    $picker = New-Object System.Windows.Forms.OpenFileDialog
    $picker.Title = "Select the full Windows AMD64 tunnel-client.exe"
    $picker.Filter = "tunnel-client.exe|tunnel-client.exe|Executable files (*.exe)|*.exe"
    $picker.CheckFileExists = $true
    if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        Stop-WithMessage "No tunnel client was selected. Download the full Windows AMD64/x64 tunnel-client first."
    }
    $clientPath = $picker.FileName
}

if ([IO.Path]::GetFileName($clientPath) -ne "tunnel-client.exe") {
    Stop-WithMessage "The selected file is not named tunnel-client.exe. Select the full OpenAI tunnel client, not the ARM64 or Cloudflare runtime package."
}

Write-Host "Selected client: $clientPath" -ForegroundColor Green
Write-Host ""
$tunnelId = Read-Host "Paste the tunnel ID for My Local Memory"
if ([string]::IsNullOrWhiteSpace($tunnelId)) {
    Stop-WithMessage "A tunnel ID is required. Copy it from the My Local Memory tunnel page."
}

$secureKey = Read-Host "Paste the restricted Runtime API key" -AsSecureString
$env:CONTROL_PLANE_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
$env:AGENTIC_MEMORY_MCP_TOKEN = "local-only-startup-guard"

$profile = "local-memory"
$mcpCommand = "py `"$(Join-Path $projectRoot 'mcp_server.py')`" stdio"

Write-Host ""
Write-Host "Creating the local profile..." -ForegroundColor Cyan
& $clientPath init --sample sample_mcp_stdio_local --profile $profile --tunnel-id $tunnelId --mcp-command $mcpCommand
$initExit = $LASTEXITCODE

if ($initExit -ne 0) {
    Write-Host "The profile may already exist. Checking it now..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Checking the tunnel configuration..." -ForegroundColor Cyan
& $clientPath doctor --profile $profile --explain
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "The tunnel configuration did not pass its check. Confirm that the tunnel ID, Runtime API key, and full AMD64 tunnel client are correct."
}

Write-Host ""
Write-Host "The tunnel is ready. Starting it now..." -ForegroundColor Green
Write-Host "Keep this window open while ChatGPT uses the memory tools. Press Ctrl+C to stop."
Write-Host ""
& $clientPath run --profile $profile

