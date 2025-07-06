import os
from dotenv import load_dotenv
import sys

# Load environment variables from .env file if it exists
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# OpenAI API Configuration
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")

# Default Model
MODEL = os.getenv("MODEL") or os.getenv("LLM_MODEL_ID") or "local-model"

# Application Details (exact match to TypeScript)
CLIENT_NAME = "mcp-server-client"
CLIENT_VERSION = "1.0.0"

# MCP configuration (exact match to TypeScript)
NODE_ENV = os.getenv("NODE_ENV", "development")

# MCP Server URL - equivalent to TypeScript MCP_SERVER_URL
MCP_SERVER_URL = (
    "./dist/src/mcp-server/index.js"
    if NODE_ENV == "production"
    else "./src/mcp-server/index.ts"
)

# Port configuration - changed from 80 to 8000 to avoid permission issues
PORT = int(os.getenv("PORT", "8000"))

# Validate that essential configurations are present
if not LLM_API_KEY:
    print("Warning: LLM_API_KEY is not set. The application may not function correctly.", file=sys.stderr) 