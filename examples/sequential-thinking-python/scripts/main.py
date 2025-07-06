#!/usr/bin/env python3

import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.prompt import prompt
from app.prompt_types import PromptPayload
from app.constants import PORT, NODE_ENV

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Sequential Thinking Agent (Exact Python)",
    version="0.2.0",
    description="Exact Python equivalent of the TypeScript sequential thinking agent"
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health check
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": asyncio.get_event_loop().time()
    }


class ExtendedPromptPayload(PromptPayload):
    ping: Optional[bool] = None


async def handle_prompt(request: Request) -> StreamingResponse:
    """Handle prompt requests - exact equivalent of TypeScript handlePrompt"""
    try:
        payload = await request.json()
        print(f"DEBUG: Received payload: {payload}", file=sys.stderr)
        print(f"DEBUG: Payload keys: {list(payload.keys())}", file=sys.stderr)
        
        # Remove any unexpected keys before creating PromptPayload
        expected_keys = {'messages', 'model', 'temperature', 'max_tokens', 'streaming'}
        filtered_payload = {k: v for k, v in payload.items() if k in expected_keys}
        print(f"DEBUG: Filtered payload: {filtered_payload}", file=sys.stderr)
        
        extended_payload = ExtendedPromptPayload(**filtered_payload)
        
        if extended_payload.ping:
            return Response(content="online", media_type="text/plain")
        
        # Set headers for SSE
        async def stream_response():
            try:
                print("Starting streaming response", file=sys.stderr)
                
                async for chunk in prompt(extended_payload):
                    yield chunk
                    
                    # Flush the response
                    if hasattr(request, 'flush'):
                        request.flush()
                        
                print("Stream complete", file=sys.stderr)
                yield b"data: [DONE]\n\n"
                
            except Exception as error:
                print(f"Stream processing error: {error}", file=sys.stderr)
                error_data = {
                    "type": "error",
                    "error": str(error) if isinstance(error, Exception) else "Unknown error"
                }
                yield f"data: {json.dumps(error_data)}\n\n".encode("utf-8")
        
        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as error:
        print(f"prompt: error {error}", file=sys.stderr)
        return Response(
            status_code=500,
            content=json.dumps({"error": str(error)}),
            media_type="application/json"
        )


@app.post("/prompt")
async def prompt_endpoint(request: Request):
    return await handle_prompt(request)


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled error: {exc}", file=sys.stderr)
    return Response(
        status_code=500,
        content=json.dumps({
            "error": str(exc),
            "stack": None if NODE_ENV == "production" else str(exc.__traceback__)
        }),
        media_type="application/json"
    )


if __name__ == "__main__":
    print(f"Server running on http://localhost:{PORT}", file=sys.stderr)
    print(f"Environment: {NODE_ENV}", file=sys.stderr)
    
    uvicorn.run(
        "scripts.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=NODE_ENV == "development"
    ) 