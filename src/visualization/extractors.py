from utils import Scope, TraceNode


def extract_generic(scope: Scope) -> TraceNode:
    return TraceNode(
        id=scope.uuid,
        parent_id=scope.parent_uuid,
        type=scope.category,
        name=scope.name,
    )


def extract_agent(scope: Scope) -> TraceNode:
    node = TraceNode(
        id=scope.uuid,
        parent_id=scope.parent_uuid,
        type="agent",
        name="Agent",
    )

    if scope.start_event:
        node.input = scope.start_event.get("data")

    if scope.end_event:
        node.output = scope.end_event.get("data")

    return node


def extract_llm(scope: Scope) -> TraceNode:
    node = TraceNode(
        id=scope.uuid,
        parent_id=scope.parent_uuid,
        type="llm",
        name=scope.name,
    )

    request = (
        scope.start_event
        .get("category_profile", {})
        .get("annotated_request", {})
    )

    response = (
        scope.end_event
        .get("category_profile", {})
        .get("annotated_response", {})
    )

    node.input = {
        "model": request.get("model"),
        "messages": request.get("messages", []),
    }

    node.output = {
        "message": response.get("message"),
        "tool_calls": response.get("tool_calls", []),
        "finish_reason": response.get("finish_reason"),
        "usage": response.get("usage"),
    }

    return node


def extract_tool(scope: Scope) -> TraceNode:
    node = TraceNode(
        id=scope.uuid,
        parent_id=scope.parent_uuid,
        type="tool",
        name=scope.name,
    )

    if scope.start_event:
        node.input = scope.start_event.get("data", {})

    if scope.end_event:
        raw = scope.end_event.get("data") or {}
        tool_message = raw.get("data") or {}

        node.output = {
            "result": tool_message.get("content"),
            "status": tool_message.get("status"),
            "tool_call_id": tool_message.get("tool_call_id"),
        }

    return node


def extract(scope: Scope) -> TraceNode:
    if scope.category == "agent":
        return extract_agent(scope)

    if scope.category == "llm":
         return extract_llm(scope)

    if scope.category == "tool":
        return extract_tool(scope)

    return extract_generic(scope)