import asyncio
import json
import os
import sys
import datetime
from typing import List, Dict, Any, Union, AsyncGenerator
from pathlib import Path

from openai import OpenAI, AsyncOpenAI

from app.constants import (
    LLM_API_KEY,
    LLM_BASE_URL,
    MODEL,
    CLIENT_NAME,
    CLIENT_VERSION,
    NODE_ENV,
)
from app.utils import (
    convert_mcp_tools_to_openai_format,
    ensure_connection,
    process_tool_calls,
    enqueue_message,
    remove_think,
)
from app.prompt_types import PromptPayload
from app.mcp_server import sequential_thinking

# Initialize OpenAI client with retry configuration
if LLM_BASE_URL:
    # For local LLMs, API key is optional
    openai_client = OpenAI(
        api_key=LLM_API_KEY or "dummy-key",  # Use dummy key for local models
        base_url=LLM_BASE_URL,
        max_retries=3,
    )
    async_openai_client = AsyncOpenAI(
        api_key=LLM_API_KEY or "dummy-key",  # Use dummy key for local models
        base_url=LLM_BASE_URL,
        max_retries=3,
    )
else:
    # For OpenAI API, API key is required
    if not LLM_API_KEY:
        raise ValueError("LLM_API_KEY is required when not using a local base URL")
    openai_client = OpenAI(api_key=LLM_API_KEY, max_retries=3)
    async_openai_client = AsyncOpenAI(api_key=LLM_API_KEY, max_retries=3)

# Load system prompt
current_dir = Path(__file__).parent
system_prompt_path = current_dir.parent / "system-prompt.txt"

try:
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    print(f"Error: System prompt file not found at {system_prompt_path}", file=sys.stderr)
    SYSTEM_PROMPT = "You are a helpful AI assistant."


async def prompt(payload: PromptPayload) -> AsyncGenerator[bytes, None]:
    """Main prompt function that interacts with OpenAI and the MCP server."""
    print(f"Starting prompt with payload: {payload}", file=sys.stderr)

    if not payload.messages:
        raise ValueError("No messages provided in payload")

    try:
        # Get available tools from FastMCP server
        available_tools = await sequential_thinking._mcp_list_tools()
        openai_tools = convert_mcp_tools_to_openai_format(available_tools)

        # Add current time to the system prompt
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_prompt_with_time = (
            SYSTEM_PROMPT
            + f"\nThe current time is {current_time} (only use this information for time-aware responses, actions)."
        )

        # Initialize messages with system message and user payload
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt_with_time},
        ]
        
        # Convert payload messages to dict format
        for msg in payload.messages:
            if hasattr(msg, '__dict__'):
                messages.append(msg.__dict__)
            elif isinstance(msg, dict):
                messages.append(msg)
            else:
                # Convert to dict if it's a dataclass or other object
                messages.append({
                    "role": getattr(msg, "role", "user"),
                    "content": getattr(msg, "content", str(msg)),
                })

        finished = False

        while not finished:
            params = {
                "model": MODEL,
                "messages": messages,
                "temperature": 0,
                "stream": True,
                "seed": 42,
                "tools": openai_tools,
            }

            stream_content = ""
            tool_calls = []

            try:
                stream = await async_openai_client.chat.completions.create(**params)

                async for chunk in stream:
                    choice = chunk.choices[0]
                    
                    if choice.delta and choice.delta.tool_calls:
                        for tool_call in choice.delta.tool_calls:
                            if tool_call.function.name:
                                tool_calls.append({
                                    "id": f"call-{datetime.datetime.now().timestamp()}",
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments or "",
                                    },
                                    "type": "function",
                                })
                            else:
                                tool_calls[-1]["function"]["arguments"] += tool_call.function.arguments
                        continue

                    if choice.delta.content:
                        stream_content += choice.delta.content
                        yield f"data: {json.dumps(enqueue_message(False, choice.delta.content))}\n\n".encode("utf-8")

                    if choice.finish_reason == "stop":
                        print(f"Finish reason: {choice.finish_reason}", file=sys.stderr)
                        finished = True

                if tool_calls and len(tool_calls) > 0:
                    finished = False

                    # Refine the function call arguments
                    for call in tool_calls:
                        call["function"]["arguments"] = call["function"]["arguments"] or "{}"

                    messages.append({
                        "role": "assistant",
                        "content": remove_think(stream_content or ""),
                        "tool_calls": tool_calls,
                    })

                    for call in tool_calls:
                        tool_call_id = call["id"]
                        tool_call_name = call["function"]["name"]
                        tool_call_args = call["function"]["arguments"] or "{}"
                        tool_result = ""

                        yield f"data: {json.dumps(enqueue_message(False, f'<action>Executing {tool_call_name}</action>'))}\n\n".encode("utf-8")

                        tool_call_args_md = "```json\n" + tool_call_args + "\n```"
                        yield f"data: {json.dumps(enqueue_message(False, f'<details><summary>Arguments</summary>{tool_call_args_md}</details>'))}\n\n".encode("utf-8")

                        try:
                            results = await process_tool_calls([call], sequential_thinking)
                            tool_result = results[0] if results else ""
                        except Exception as err:
                            tool_result = f"Error executing tool: {str(err)}"

                        tool_result_md = "```json\n" + tool_result + "\n```"
                        yield f"data: {json.dumps(enqueue_message(False, f'<details><summary>Response</summary>{tool_result_md}</details>'))}\n\n".encode("utf-8")

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": tool_result,
                        })
            except Exception as stream_error:
                print(f"Error in streaming: {stream_error}", file=sys.stderr)
                raise stream_error

        yield f"data: {json.dumps(enqueue_message(True, ''))}\n\n".encode("utf-8")

    except Exception as error:
        print(f"Error in prompt execution: {error}", file=sys.stderr)
        raise ValueError(
            f"Failed to execute prompt: {error if isinstance(error, str) else str(error)}"
        ) 