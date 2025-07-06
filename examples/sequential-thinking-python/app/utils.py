import json
import re
import asyncio
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI

from app.constants import MODEL


def convert_mcp_tools_to_openai_format(mcp_tools: Union[List[Dict[str, Any]], List[Any]]) -> List[Dict[str, Any]]:
    """Convert MCP tool format to OpenAI tool format - exact equivalent of TypeScript version"""
    tools_list = (
        mcp_tools
        if isinstance(mcp_tools, list)
        else mcp_tools.get("tools", [])
        if isinstance(mcp_tools, dict) and "tools" in mcp_tools
        else []
    )

    return [
        {
            "type": "function",
            "function": {
                "name": tool.get("name") if isinstance(tool, dict) else getattr(tool, "name", None),
                "description": tool.get("description") if isinstance(tool, dict) else getattr(tool, "description", None),
                "parameters": tool.get("inputSchema", {}) if isinstance(tool, dict) else getattr(tool, "inputSchema", {}),
            },
        }
        for tool in tools_list
        if (isinstance(tool, dict) and "name" in tool and "description" in tool) or 
           (hasattr(tool, "name") and hasattr(tool, "description"))
    ]


async def process_tool_calls(
    tool_calls: List[Dict[str, Any]], client: Any
) -> List[str]:
    """Process tool calls using FastMCP client - exact equivalent of TypeScript version"""
    results: List[str] = []

    for call in tool_calls:
        name = call.get("function", {}).get("name")
        args = call.get("function", {}).get("arguments", "{}")

        try:
            parsed_args = json.loads(args)
            # Use FastMCP's tool calling mechanism
            if hasattr(client, "_mcp_call_tool"):
                res = await client._mcp_call_tool(key=name, arguments=parsed_args)
            else:
                # Fallback for other client types
                res = await client.call_tool(name=name, arguments=parsed_args)

            # Handle the result format - it can be a list of ContentBlocks or a tuple
            if isinstance(res, tuple):
                content_blocks, structured_output = res
            else:
                content_blocks = res
                structured_output = {}
            
            # Convert to the expected format
            if content_blocks and len(content_blocks) > 0:
                # Extract text from the first content block
                first_block = content_blocks[0]
                if hasattr(first_block, 'text'):
                    text = first_block.text
                else:
                    text = str(first_block)
                results.append(text)
            else:
                results.append("")
        except Exception as error:
            results.append(
                f"Error executing tool {name}: {str(error)}"
            )

    return results


async def ensure_connection(
    client: Any, transport: Any, retries: int = 3
) -> None:
    """Ensure connection to MCP server - exact equivalent of TypeScript version"""
    for attempt in range(retries):
        try:
            # Check if client is connected by trying to ping
            if hasattr(client, "ping"):
                await client.ping()
            return
        except Exception:
            if attempt == retries - 1:
                raise ValueError(
                    f"Failed to connect to MCP server after {retries} attempts"
                )
            await asyncio.sleep(1000 * (2 ** attempt) / 1000)  # Convert to seconds


def enqueue_message(
    stop: bool, content: str, role: str = "assistant"
) -> Dict[str, Any]:
    """Format message for streaming - exact equivalent of TypeScript version"""
    return {
        "id": f"chatcmpl-{int(asyncio.get_event_loop().time() * 1000)}",
        "object": "chat.completion.chunk",
        "created": int(asyncio.get_event_loop().time() * 1000),
        "model": MODEL,
        "choices": [
            {
                "index": 0,
                "delta": {
                    "content": content,
                    "role": role,
                },
                "logprobs": None,
                "finish_reason": "stop" if stop else None,
            }
        ],
    }


def remove_think(content: str) -> str:
    """Remove <think>...</think> tags from content - exact equivalent of TypeScript version"""
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL) 