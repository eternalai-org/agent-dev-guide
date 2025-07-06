#!/usr/bin/env python3

import asyncio
import json
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from termcolor import colored
from pathlib import Path

from fastmcp import FastMCP

from app.constants import MCP_SERVER_URL

# Environment variable to disable thought logging
DISABLE_THOUGHT_LOGGING = os.getenv("DISABLE_THOUGHT_LOGGING", "false").lower() == "true"


@dataclass
class ThoughtData:
    thought: str
    thought_number: int
    total_thoughts: int
    next_thought_needed: bool
    is_revision: Optional[bool] = None
    revises_thought: Optional[int] = None
    branch_from_thought: Optional[int] = None
    branch_id: Optional[str] = None
    needs_more_thoughts: Optional[bool] = None


class SequentialThinkingServer:
    def __init__(self):
        self.thought_history: List[ThoughtData] = []
        self.branches: Dict[str, List[ThoughtData]] = {}
        self.disable_thought_logging = DISABLE_THOUGHT_LOGGING

    def _validate_thought_data(self, input_data: Dict[str, Any]) -> ThoughtData:
        data = input_data

        if not data.get("thought") or not isinstance(data["thought"], str):
            raise ValueError("Invalid thought: must be a string")
        if not data.get("thoughtNumber") or not isinstance(data["thoughtNumber"], int):
            raise ValueError("Invalid thoughtNumber: must be a number")
        if not data.get("totalThoughts") or not isinstance(data["totalThoughts"], int):
            raise ValueError("Invalid totalThoughts: must be a number")
        if not isinstance(data.get("nextThoughtNeeded"), bool):
            raise ValueError("Invalid nextThoughtNeeded: must be a boolean")

        return ThoughtData(
            thought=data["thought"],
            thought_number=data["thoughtNumber"],
            total_thoughts=data["totalThoughts"],
            next_thought_needed=data["nextThoughtNeeded"],
            is_revision=data.get("isRevision"),
            revises_thought=data.get("revisesThought"),
            branch_from_thought=data.get("branchFromThought"),
            branch_id=data.get("branchId"),
            needs_more_thoughts=data.get("needsMoreThoughts"),
        )

    def _format_thought(self, thought_data: ThoughtData) -> str:
        thought_number = thought_data.thought_number
        total_thoughts = thought_data.total_thoughts
        thought = thought_data.thought
        is_revision = thought_data.is_revision
        revises_thought = thought_data.revises_thought
        branch_from_thought = thought_data.branch_from_thought
        branch_id = thought_data.branch_id

        prefix = ""
        context = ""

        if is_revision:
            prefix = colored("🔄 Revision", "yellow")
            context = f" (revising thought {revises_thought})"
        elif branch_from_thought:
            prefix = colored("🌿 Branch", "green")
            context = f" (from thought {branch_from_thought}, ID: {branch_id})"
        else:
            prefix = colored("💭 Thought", "blue")
            context = ""

        header = f"{prefix} {thought_number}/{total_thoughts}{context}"
        border = "─" * (max(len(header), len(thought)) + 4)

        return f"""
┌{border}┐
│ {header} │
├{border}┤
│ {thought.ljust(len(border) - 2)} │
└{border}┘"""

    def process_thought(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated_input = self._validate_thought_data(input_data)

            if validated_input.thought_number > validated_input.total_thoughts:
                validated_input.total_thoughts = validated_input.thought_number

            self.thought_history.append(validated_input)

            if validated_input.branch_from_thought and validated_input.branch_id:
                if validated_input.branch_id not in self.branches:
                    self.branches[validated_input.branch_id] = []
                self.branches[validated_input.branch_id].append(validated_input)

            if not self.disable_thought_logging:
                formatted_thought = self._format_thought(validated_input)
                print(formatted_thought, file=sys.stderr, flush=True)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "thoughtNumber": validated_input.thought_number,
                                "totalThoughts": validated_input.total_thoughts,
                                "nextThoughtNeeded": validated_input.next_thought_needed,
                                "branches": list(self.branches.keys()),
                                "thoughtHistoryLength": len(self.thought_history),
                            },
                            indent=2
                        ),
                    }
                ]
            }
        except Exception as error:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "error": str(error),
                                "status": "failed",
                            },
                            indent=2
                        ),
                    }
                ],
                "isError": True,
            }


# Initialize FastMCP client
sequential_thinking = FastMCP(name="sequential-thinking-server")

# Global connection state
is_connected = False


async def ensure_mcp_connection():
    """Ensure MCP server connection is established"""
    global is_connected
    
    if not is_connected:
        try:
            # FastMCP doesn't have a connect method, it connects automatically
            # Just verify we can list tools to test connection
            await sequential_thinking._mcp_list_tools()
            is_connected = True
            print("Connected to MCP server", file=sys.stderr)
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}", file=sys.stderr)
            raise


async def get_available_tools() -> List[Dict[str, Any]]:
    """Get available tools from MCP server"""
    await ensure_mcp_connection()
    tools = await sequential_thinking._mcp_list_tools()
    # Convert Tool objects to dict format
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.parameters
        }
        for tool in tools
    ]


async def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call a tool on the MCP server"""
    await ensure_mcp_connection()
    result = await sequential_thinking._mcp_call_tool(key=name, arguments=arguments)
    
    # Handle the result format - it can be a list of ContentBlocks or a tuple
    if isinstance(result, tuple):
        content_blocks, structured_output = result
    else:
        content_blocks = result
        structured_output = {}
    
    # Convert to the expected format
    if content_blocks and len(content_blocks) > 0:
        # Extract text from the first content block
        first_block = content_blocks[0]
        if hasattr(first_block, 'text'):
            text = first_block.text
        else:
            text = str(first_block)
        return {"content": [{"text": text}]}
    else:
        return {"content": [{"text": ""}]}


# Create server instance
thinking_server = SequentialThinkingServer()


@sequential_thinking.tool(
    name="sequentialthinking",
    description="""A detailed tool for dynamic and reflective problem-solving through thoughts.
This tool helps analyze problems through a flexible thinking process that can adapt and evolve.
Each thought can build on, question, or revise previous insights as understanding deepens.

When to use this tool:
- Breaking down complex problems into steps
- Planning and design with room for revision
- Analysis that might need course correction
- Problems where the full scope might not be clear initially
- Problems that require a multi-step solution
- Tasks that need to maintain context over multiple steps
- Situations where irrelevant information needs to be filtered out

Key features:
- You can adjust total_thoughts up or down as you progress
- You can question or revise previous thoughts
- You can add more thoughts even after reaching what seemed like the end
- You can express uncertainty and explore alternative approaches
- Not every thought needs to build linearly - you can branch or backtrack
- Generates a solution hypothesis
- Verifies the hypothesis based on the Chain of Thought steps
- Repeats the process until satisfied
- Provides a correct answer

Parameters explained:
- thought: Your current thinking step, which can include:
* Regular analytical steps
* Revisions of previous thoughts
* Questions about previous decisions
* Realizations about needing more analysis
* Changes in approach
* Hypothesis generation
* Hypothesis verification
- next_thought_needed: True if you need more thinking, even if at what seemed like the end
- thought_number: Current number in sequence (can go beyond initial total if needed)
- total_thoughts: Current estimate of thoughts needed (can be adjusted up/down)
- is_revision: A boolean indicating if this thought revises previous thinking
- revises_thought: If is_revision is true, which thought number is being reconsidered
- branch_from_thought: If branching, which thought number is the branching point
- branch_id: Identifier for the current branch (if any)
- needs_more_thoughts: If reaching end but realizing more thoughts needed

You should:
1. Start with an initial estimate of needed thoughts, but be ready to adjust
2. Feel free to question or revise previous thoughts
3. Don't hesitate to add more thoughts if needed, even at the "end"
4. Express uncertainty when present
5. Mark thoughts that revise previous thinking or branch into new paths
6. Ignore information that is irrelevant to the current step
7. Generate a solution hypothesis when appropriate
8. Verify the hypothesis based on the Chain of Thought steps
9. Repeat the process until satisfied with the solution
10. Provide a single, ideally correct answer as the final output
11. Only set next_thought_needed to false when truly done and a satisfactory answer is reached""",
    annotations={
        "thought": "Your current thinking step",
        "nextThoughtNeeded": "Whether another thought step is needed",
        "thoughtNumber": "Current thought number",
        "totalThoughts": "Estimated total thoughts needed",
        "isRevision": "Whether this revises previous thinking",
        "revisesThought": "Which thought is being reconsidered",
        "branchFromThought": "Branching point thought number",
        "branchId": "Branch identifier",
        "needsMoreThoughts": "If more thoughts are needed",
    }
)
async def sequential_thinking_tool(
    thought: str,
    nextThoughtNeeded: bool,
    thoughtNumber: int,
    totalThoughts: int,
    isRevision: Optional[bool] = None,
    revisesThought: Optional[int] = None,
    branchFromThought: Optional[int] = None,
    branchId: Optional[str] = None,
    needsMoreThoughts: Optional[bool] = None,
) -> str:
    """Sequential thinking tool - exact equivalent of TypeScript version"""
    input_data = {
        "thought": thought,
        "nextThoughtNeeded": nextThoughtNeeded,
        "thoughtNumber": thoughtNumber,
        "totalThoughts": totalThoughts,
        "isRevision": isRevision,
        "revisesThought": revisesThought,
        "branchFromThought": branchFromThought,
        "branchId": branchId,
        "needsMoreThoughts": needsMoreThoughts,
    }
    
    result = thinking_server.process_thought(input_data)
    
    if result.get("isError"):
        return result["content"][0]["text"]
    
    return result["content"][0]["text"]


if __name__ == "__main__":
    # Run the FastMCP server
    sequential_thinking.run() 