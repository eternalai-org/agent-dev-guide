# Sequential Thinking Agent (Exact Python Version)

This is an **exact Python equivalent** of the TypeScript sequential-thinking agent that uses the MCP (Model Context Protocol) framework. Unlike the previous Python version that used HTTP endpoints, this version uses the same MCP protocol as the TypeScript version.

## Key Differences from Previous Python Version

### ✅ **Exact MCP Protocol Implementation**
- Uses the official Python MCP SDK (`mcp` package)
- Implements proper MCP server with `stdio_server`
- Uses `stdio_client` for MCP communication
- MCP server runs as a separate process via stdio communication

### ✅ **Identical Architecture to TypeScript**
- **MCP Server**: `app/mcp_server.py` (equivalent to `src/mcp-server/index.ts`)
- **MCP Client**: `app/prompt.py` (equivalent to `src/prompt/index.ts`)
- **Utils**: `app/utils.py` (equivalent to `src/utils.ts`)
- **Constants**: `app/constants.py` (equivalent to `src/constants.ts`)
- **Server**: `scripts/main.py` (equivalent to `scripts/main.ts`)

### ✅ **Same Communication Protocol**
- Uses MCP stdio transport instead of HTTP
- Tool calls go through MCP protocol, not HTTP endpoints
- Identical error handling and message formatting

## Quick Start

### 1. Install Dependencies

```bash
cd examples/sequential-thinking-python
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Development Mode

Start the agent in development mode:

```bash
python scripts/main.py
```

### 3. Add or Modify Tool Calls

You can add or customize tool calls in:

```
examples/sequential-thinking-python/app/mcp_server.py
```

Edit this file to register new tools or change existing ones.

### 4. Configure Environment Variables

Create a `.env` file in the `examples/sequential-thinking-python` directory:

```env
LLM_BASE_URL=http://localhost:65534  # Your local LLM server URL
MODEL=local-model  # Optional, defaults to "local-model"
NODE_ENV=development
PORT=8808  # Optional, defaults to 8000
```

**Note:** Since this is designed to work with local LLMs, no API key is required. The `LLM_BASE_URL` should point to your local LLM server.

### 5. Test the MCP Server

You can test the MCP server directly:

```bash
python app/mcp_server.py
```

## Architecture Comparison

| Component | TypeScript | Python (Exact) | Python (Previous) |
|-----------|------------|----------------|-------------------|
| **Protocol** | MCP stdio | MCP stdio | HTTP |
| **Server** | Express.js | FastAPI | FastAPI |
| **MCP Server** | `src/mcp-server/index.ts` | `app/mcp_server.py` | `app/mcp_server.py` |
| **Tool Calls** | MCP protocol | MCP protocol | HTTP endpoints |
| **Communication** | stdio | stdio | HTTP |

## Key Features

- **Identical MCP Implementation**: Uses the same MCP protocol as TypeScript
- **Same Tool Definition**: Exact copy of the sequentialthinking tool
- **Identical Message Formatting**: Same `enqueue_message` function
- **Same Error Handling**: Identical error propagation
- **Same Streaming**: Identical SSE streaming implementation
- **Same Validation**: Identical input validation logic

## File Structure

```
examples/sequential-thinking-python/
├── app/
│   ├── mcp_server.py      # MCP server (equiv to src/mcp-server/index.ts)
│   ├── prompt.py          # MCP client (equiv to src/prompt/index.ts)
│   ├── utils.py           # Utils (equiv to src/utils.ts)
│   ├── constants.py       # Constants (equiv to src/constants.ts)
│   └── prompt_types.py    # Type definitions
├── scripts/
│   └── main.py            # Main server (equiv to scripts/main.ts)
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Testing

Test the MCP server:

```bash
# Test the MCP server directly
python app/mcp_server.py

# Test the full application
python scripts/main.py
```

Then send a request to `http://localhost:80/prompt`:

```bash
curl -X POST "http://localhost:80/prompt" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Think step by step about solving a complex problem."}]}' \
  --no-buffer
```

## Summary

- **Development:** `python scripts/main.py`
- **Add tools:** Edit `app/mcp_server.py`
- **Configure:** Update environment variables
- **Protocol:** MCP stdio (identical to TypeScript)

This version provides **exact functional equivalence** to the TypeScript version while maintaining Python's syntax and ecosystem benefits. 