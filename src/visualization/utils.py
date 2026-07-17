from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceNode:
    id: str
    parent: str | None

    type: str            # agent | llm | tool | user | system
    name: str

    content: Any = None
    input: Any = None
    output: Any = None

    start_time: float | None = None
    end_time: float | None = None

    children: list["TraceNode"] = field(default_factory=list)


@dataclass
class Scope:
    uuid: str
    parent_uuid: str | None
    name: str
    category: str

    start_event: dict[str, Any] | None = None
    end_event: dict[str, Any] | None = None
    children: list["Scope"] = field(default_factory=list)



@dataclass
class TraceNode:
    id: str
    parent_id: str | None

    type: str
    name: str

    input: Any = None
    output: Any = None
    content: Any = None

    metadata: dict = field(default_factory=dict)

    children: list["TraceNode"] = field(default_factory=list)
