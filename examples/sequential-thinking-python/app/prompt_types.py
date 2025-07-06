from typing import Dict, List, Any, Union, Optional
from dataclasses import dataclass


@dataclass
class ContentPart:
    type: str
    text: Optional[str] = None
    image_url: Optional[Dict[str, Any]] = None


Content = Union[str, List[ContentPart]]


@dataclass
class BaseMessage:
    role: str
    content: Content


@dataclass
class ToolMessage(BaseMessage):
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    
    def __post_init__(self):
        self.role = "tool"


Message = Union[BaseMessage, ToolMessage]


@dataclass
class PromptPayload:
    messages: List[Message]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    streaming: Optional[bool] = None 