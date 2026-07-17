from copy import deepcopy

from utils import TraceNode


FRAMEWORK_NODES = {
    "LangGraph",
    "model",
    "tools",
}


def simplify(root: TraceNode) -> TraceNode:
    """
    Convert the parser tree into a presentation tree.

    Example:

        agent-turn
        └── LangGraph
            ├── model
            │   └── demo
            ├── tools
            │   └── get_current_weather
            └── model
                └── demo

    becomes

        agent-turn
        ├── LLM
        │   └── get_current_weather
        └── LLM
    """

    root = deepcopy(root)

    _simplify(root)

    return root


def _simplify(node: TraceNode) -> None:
    # First simplify children recursively
    for child in node.children:
        _simplify(child)

    # Remove framework nodes
    node.children = _flatten(node.children)

    # Rename semantic nodes
    for child in node.children:
        if child.type == "agent" and child.name == "agent-turn":
            child.name = "Agent"

        elif child.type == "llm":
            finish = (child.output or {}).get("finish_reason")

            child.name = (
                "LLM (tool_use)"
                if finish == "tool_use"
                else "LLM"
            )

    # Attach tools underneath the LLM that requested them
    node.children = _attach_tools(node.children)


def _flatten(children: list[TraceNode]) -> list[TraceNode]:
    """
    Recursively remove framework nodes while preserving
    the semantic nodes beneath them.
    """

    flattened = []

    for child in children:

        if child.name in FRAMEWORK_NODES:
            # recurse into the promoted children
            flattened.extend(_flatten(child.children))
        else:
            flattened.append(child)

    return flattened


def _attach_tools(children: list[TraceNode]) -> list[TraceNode]:
    """
    Convert

        LLM(tool_use)
        Tool
        LLM

    into

        LLM(tool_use)
            Tool
        LLM
    """

    result = []

    previous_llm = None

    for child in children:

        if child.type == "llm":
            previous_llm = child
            result.append(child)
            continue

        if child.type == "tool":

            if (
                previous_llm is not None
                and previous_llm.output is not None
                and previous_llm.output.get("finish_reason") == "tool_use"
            ):
                previous_llm.children.append(child)
            else:
                result.append(child)

            continue

        result.append(child)

    return result