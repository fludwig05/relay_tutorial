from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Iterable

from utils import TraceNode


def write_trace_html(
    trace_roots: Iterable[TraceNode],
    output_path: str | Path,
    *,
    title: str = "Agent Trace",
) -> Path:
    """
    Render TraceNode roots as a self-contained HTML document.

    The generated file has no external dependencies and can be opened
    directly in a browser.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    roots = list(trace_roots)

    document = _render_document(
        trace_roots=roots,
        title=title,
    )

    output_path.write_text(document, encoding="utf-8")

    return output_path


def _render_document(
    trace_roots: list[TraceNode],
    title: str,
) -> str:
    rendered_roots = "\n".join(
        _render_node(root, depth=0)
        for root in trace_roots
    )

    empty_state = """
        <div class="empty-state">
            No trace nodes were found.
        </div>
    """

    body = rendered_roots if rendered_roots else empty_state

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>{html.escape(title)}</title>

    <style>
        :root {{
            color-scheme: light dark;

            --page-background: #f4f6f8;
            --card-background: #ffffff;
            --card-border: #dfe3e8;
            --card-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);

            --text-primary: #172033;
            --text-secondary: #667085;
            --text-muted: #98a2b3;

            --agent-color: #7c3aed;
            --agent-background: #f5f3ff;

            --llm-color: #2563eb;
            --llm-background: #eff6ff;

            --tool-color: #059669;
            --tool-background: #ecfdf5;

            --generic-color: #64748b;
            --generic-background: #f8fafc;

            --connector-color: #cbd5e1;
            --code-background: #101828;
            --code-text: #e4e7ec;
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                --page-background: #0b0f17;
                --card-background: #131a25;
                --card-border: #263244;
                --card-shadow: none;

                --text-primary: #f2f4f7;
                --text-secondary: #98a2b3;
                --text-muted: #667085;

                --agent-background: rgba(124, 58, 237, 0.14);
                --llm-background: rgba(37, 99, 235, 0.14);
                --tool-background: rgba(5, 150, 105, 0.14);
                --generic-background: rgba(100, 116, 139, 0.12);

                --connector-color: #344054;
                --code-background: #070b12;
                --code-text: #d0d5dd;
            }}
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            background: var(--page-background);
            color: var(--text-primary);
            font-family:
                Inter,
                ui-sans-serif,
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }}

        .page {{
            width: min(1100px, calc(100% - 32px));
            margin: 0 auto;
            padding: 40px 0 80px;
        }}

        .page-header {{
            margin-bottom: 28px;
        }}

        .page-title {{
            margin: 0;
            font-size: 30px;
            font-weight: 720;
            letter-spacing: -0.03em;
        }}

        .page-subtitle {{
            margin: 8px 0 0;
            color: var(--text-secondary);
            font-size: 14px;
        }}

        .trace-root {{
            margin-bottom: 22px;
        }}

        .trace-node {{
            position: relative;
        }}

        .node-card {{
            position: relative;
            overflow: hidden;
            background: var(--card-background);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            box-shadow: var(--card-shadow);
        }}

        .node-card::before {{
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            width: 4px;
            content: "";
            background: var(--generic-color);
        }}

        .node-card.agent::before {{
            background: var(--agent-color);
        }}

        .node-card.llm::before {{
            background: var(--llm-color);
        }}

        .node-card.tool::before {{
            background: var(--tool-color);
        }}

        .node-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            min-height: 54px;
            padding: 12px 16px 12px 19px;
        }}

        .node-icon {{
            display: grid;
            flex: 0 0 auto;
            width: 32px;
            height: 32px;
            place-items: center;
            border-radius: 8px;
            font-size: 16px;
        }}

        .node-icon.agent {{
            color: var(--agent-color);
            background: var(--agent-background);
        }}

        .node-icon.llm {{
            color: var(--llm-color);
            background: var(--llm-background);
        }}

        .node-icon.tool {{
            color: var(--tool-color);
            background: var(--tool-background);
        }}

        .node-icon.generic {{
            color: var(--generic-color);
            background: var(--generic-background);
        }}

        .node-heading {{
            min-width: 0;
            flex: 1;
        }}

        .node-name {{
            overflow: hidden;
            margin: 0;
            font-size: 14px;
            font-weight: 680;
            line-height: 1.4;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .node-type {{
            margin-top: 2px;
            color: var(--text-secondary);
            font-family:
                ui-monospace,
                SFMono-Regular,
                Menlo,
                Monaco,
                Consolas,
                monospace;
            font-size: 11px;
        }}

        .node-fields {{
            display: grid;
            gap: 10px;
            padding: 0 16px 16px 19px;
        }}

        details.data-panel {{
            overflow: hidden;
            border: 1px solid var(--card-border);
            border-radius: 8px;
        }}

        details.data-panel > summary {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 9px 11px;
            color: var(--text-secondary);
            font-size: 12px;
            font-weight: 650;
            cursor: pointer;
            list-style: none;
            user-select: none;
        }}

        details.data-panel > summary::-webkit-details-marker {{
            display: none;
        }}

        details.data-panel > summary::before {{
            content: "›";
            color: var(--text-muted);
            font-size: 18px;
            line-height: 10px;
            transform-origin: center;
            transition: transform 120ms ease;
        }}

        details.data-panel[open] > summary::before {{
            transform: rotate(90deg);
        }}

        .field-size {{
            margin-left: auto;
            color: var(--text-muted);
            font-family:
                ui-monospace,
                SFMono-Regular,
                Menlo,
                Monaco,
                Consolas,
                monospace;
            font-size: 10px;
            font-weight: 500;
        }}

        pre {{
            overflow-x: auto;
            max-height: 520px;
            margin: 0;
            padding: 14px;
            background: var(--code-background);
            color: var(--code-text);
            font-family:
                ui-monospace,
                SFMono-Regular,
                Menlo,
                Monaco,
                Consolas,
                monospace;
            font-size: 12px;
            line-height: 1.55;
            white-space: pre-wrap;
            word-break: break-word;
        }}

        .children {{
            position: relative;
            display: grid;
            gap: 12px;
            margin: 12px 0 0 26px;
            padding-left: 24px;
        }}

        .children::before {{
            position: absolute;
            top: 0;
            bottom: 18px;
            left: 5px;
            width: 1px;
            content: "";
            background: var(--connector-color);
        }}

        .children > .trace-node::before {{
            position: absolute;
            top: 27px;
            left: -19px;
            width: 19px;
            height: 1px;
            content: "";
            background: var(--connector-color);
        }}

        .status-badge {{
            flex: 0 0 auto;
            padding: 4px 7px;
            border-radius: 999px;
            background: var(--generic-background);
            color: var(--text-secondary);
            font-family:
                ui-monospace,
                SFMono-Regular,
                Menlo,
                Monaco,
                Consolas,
                monospace;
            font-size: 10px;
            font-weight: 650;
        }}

        .status-badge.success {{
            color: var(--tool-color);
            background: var(--tool-background);
        }}

        .status-badge.error {{
            color: #dc2626;
            background: rgba(220, 38, 38, 0.1);
        }}

        .empty-state {{
            padding: 60px 20px;
            color: var(--text-secondary);
            text-align: center;
            background: var(--card-background);
            border: 1px dashed var(--card-border);
            border-radius: 12px;
        }}

        @media (max-width: 640px) {{
            .page {{
                width: min(100% - 20px, 1100px);
                padding-top: 24px;
            }}

            .children {{
                margin-left: 11px;
                padding-left: 17px;
            }}

            .children > .trace-node::before {{
                left: -12px;
                width: 12px;
            }}
        }}
    </style>
</head>

<body>
    <main class="page">
        <header class="page-header">
            <h1 class="page-title">{html.escape(title)}</h1>
            <p class="page-subtitle">
                Semantic Execution Trace with.
            </p>
        </header>

        <section class="trace-list">
            {body}
        </section>
    </main>
</body>
</html>
"""


def _render_node(
    node: TraceNode,
    depth: int,
) -> str:
    node_type = str(node.type or "generic").lower()
    css_type = _css_type(node_type)
    icon = _icon_for_type(node_type)

    status = _get_status(node)
    status_html = _render_status(status)

    fields = []

    if node.input is not None:
        fields.append(
            _render_data_panel(
                label="Input",
                value=node.input,
                open_by_default=False,
            )
        )

    if node.output is not None:
        fields.append(
            _render_data_panel(
                label="Output",
                value=node.output,
                open_by_default=False,
            )
        )

    if getattr(node, "content", None) is not None:
        fields.append(
            _render_data_panel(
                label="Content",
                value=node.content,
                open_by_default=False,
            )
        )

    fields_html = ""

    if fields:
        fields_html = f"""
            <div class="node-fields">
                {''.join(fields)}
            </div>
        """

    children_html = ""

    if node.children:
        rendered_children = "\n".join(
            _render_node(child, depth=depth + 1)
            for child in node.children
        )

        children_html = f"""
            <div class="children">
                {rendered_children}
            </div>
        """

    safe_name = html.escape(str(node.name or node.type or "Unnamed node"))
    safe_type = html.escape(str(node.type or "unknown"))

    return f"""
        <article
            class="trace-node {'trace-root' if depth == 0 else ''}"
            data-node-id="{html.escape(str(node.id), quote=True)}"
            data-node-type="{html.escape(node_type, quote=True)}"
        >
            <div class="node-card {css_type}">
                <div class="node-header">
                    <div class="node-icon {css_type}">
                        {icon}
                    </div>

                    <div class="node-heading">
                        <h2 class="node-name">{safe_name}</h2>
                        <div class="node-type">{safe_type}</div>
                    </div>

                    {status_html}
                </div>

                {fields_html}
            </div>

            {children_html}
        </article>
    """


def _render_data_panel(
    label: str,
    value: Any,
    *,
    open_by_default: bool,
) -> str:
    serialized = _serialize(value)
    line_count = serialized.count("\n") + 1

    open_attribute = " open" if open_by_default else ""

    return f"""
        <details class="data-panel"{open_attribute}>
            <summary>
                {html.escape(label)}
                <span class="field-size">
                    {line_count} {"line" if line_count == 1 else "lines"}
                </span>
            </summary>

            <pre>{html.escape(serialized)}</pre>
        </details>
    """


def _serialize(value: Any) -> str:
    """
    Convert arbitrary trace data to readable JSON.

    `default=str` prevents serialization failures for exceptions,
    UUID objects, datetimes, and framework-specific values.
    """
    try:
        return json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    except (TypeError, ValueError):
        return repr(value)


def _get_status(node: TraceNode) -> str | None:
    if not isinstance(node.output, dict):
        return None

    status = node.output.get("status")

    if status is not None:
        return str(status)

    if node.type == "llm":
        finish_reason = node.output.get("finish_reason")

        if finish_reason is not None:
            return str(finish_reason)

    return None


def _render_status(status: str | None) -> str:
    if not status:
        return ""

    normalized = status.lower()

    if normalized in {"success", "complete", "completed"}:
        css_class = "success"
    elif normalized in {"error", "failed", "failure"}:
        css_class = "error"
    else:
        css_class = ""

    return (
        f'<span class="status-badge {css_class}">'
        f"{html.escape(status)}"
        f"</span>"
    )


def _css_type(node_type: str) -> str:
    if node_type in {"agent", "llm", "tool"}:
        return node_type

    return "generic"


def _icon_for_type(node_type: str) -> str:
    icons = {
        "agent": "A",
        "llm": "L",
        "tool": "T",
    }

    return icons.get(node_type, "•")