from html_conversion import write_trace_html
from utils import Scope, TraceNode
from extractors import extract
from transform import simplify
from pprint import pformat
from pathlib import Path
import json



def load_events(path):
    events = []

    with open(path) as f:
        for line in f:
            events.append(json.loads(line))

    return events


def build_scopes(events):
    """
    Merge start/end scope events into Scope objects.
    """

    scopes = {}

    for event in events:

        # Ignore marks
        if event["kind"] != "scope":
            continue

        uuid = event["uuid"]

        if uuid not in scopes:

            scopes[uuid] = Scope(
                uuid=uuid,
                parent_uuid=event.get("parent_uuid"),
                name=event["name"],
                category=event["category"],
            )

        scope = scopes[uuid]

        if event["scope_category"] == "start":
            scope.start_event = event

        elif event["scope_category"] == "end":
            scope.end_event = event

    return list(scopes.values())


def build_scope_tree(scopes: list[Scope]) -> list[Scope]:
    scope_lookup = {scope.uuid: scope for scope in scopes}

    # Important when rerunning the function
    for scope in scopes:
        scope.children.clear()

    roots = []

    for scope in scopes:
        parent = scope_lookup.get(scope.parent_uuid)

        if parent is None:
            # parent_uuid may be None or refer to an external trace/span
            roots.append(scope)
        else:
            parent.children.append(scope)

    return roots


def print_tree(scope: Scope, prefix: str = "", is_last: bool = True) -> None:
    connector = "└── " if is_last else "├── "
    print(f"{prefix}{connector}{scope.name} [{scope.category}]")

    child_prefix = prefix + ("    " if is_last else "│   ")

    for index, child in enumerate(scope.children):
        print_tree(
            child,
            prefix=child_prefix,
            is_last=index == len(scope.children) - 1,
        )


def build_trace_tree(scope: Scope) -> TraceNode:
    node = extract(scope)

    node.children = [
        build_trace_tree(child)
        for child in scope.children
    ]

    return node


def preview(value, max_len=100):
    text = pformat(value, compact=True)
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text

def print_trace(node: TraceNode, indent=0):
    print(" " * indent + f"{node.name} ({node.type})")

    if node.input:
        print(" " * (indent + 2) + f"input : {preview(node.input)}")

    if node.output:
        print(" " * (indent + 2) + f"output: {preview(node.output)}")

    for child in node.children:
        print_trace(child, indent + 4)


if __name__ == "__main__":

    # input path
    input_path = Path("/home/fludwig/Desktop/repositories/relay_tutorial/logs/events.jsonl")

    # load events from jsonl file
    events = load_events(input_path)

    # build scopes from events
    scopes = build_scopes(events)

    # build scope tree
    roots = build_scope_tree(scopes)

    trace_roots = [simplify(build_trace_tree(root)) for root in roots]

    #for trace in trace_roots:
    #    print_trace(trace)

    output_path = write_trace_html(trace_roots,Path("output") / "trace.html", title="Agent Trace")