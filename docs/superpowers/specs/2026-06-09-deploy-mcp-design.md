# 2026-06-09 RuScholar Studio MCP Deployment Design Spec

This specification outlines the configuration changes to deploy the `ruscholar-studio` Model Context Protocol (MCP) server locally within Google Antigravity.

## Proposed Changes

### Configuration Files

#### [NEW] [.env](.env)
Create the `.env` configuration file in the project root to support local/offline execution parameters for the diagnostic and polishing engines.

#### [MODIFY] [mcp_config.json](~/.gemini/config/mcp_config.json)
Configure Antigravity's global MCP config file to register the `ruscholar-studio` server.

## Verification Plan

### Manual Verification
1. Run a check to verify that `mcp_server.server` can be imported and run correctly from the terminal:
   ```bash
   PYTHONPATH=. python3 -m mcp_server.server
   ```
2. Verify that the tool definitions are successfully detected by Antigravity after registration (the agent should be able to see the new tools).
