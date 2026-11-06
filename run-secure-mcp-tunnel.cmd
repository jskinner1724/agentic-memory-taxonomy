@echo off
setlocal
cd /d "%~dp0"

if "%AGENTIC_MEMORY_TUNNEL_PROFILE%"=="" (
    echo Set AGENTIC_MEMORY_TUNNEL_PROFILE in the current PowerShell session first.
    echo Do not put the runtime key in this file or pass it on the command line.
    pause
    exit /b 1
)

where tunnel-client >nul 2>&1
if errorlevel 1 (
    echo tunnel-client is not installed or is not on PATH.
    echo Install it from the OpenAI Secure MCP Tunnel documentation, then run this launcher again.
    pause
    exit /b 1
)

echo Validating tunnel profile %AGENTIC_MEMORY_TUNNEL_PROFILE%...
tunnel-client doctor --profile "%AGENTIC_MEMORY_TUNNEL_PROFILE%" --explain
if errorlevel 1 (
    echo Tunnel profile validation failed. No tunnel was started.
    pause
    exit /b 1
)

echo Starting the outbound-only Secure MCP Tunnel. Press Ctrl+C to stop.
tunnel-client run --profile "%AGENTIC_MEMORY_TUNNEL_PROFILE%"
endlocal
