"""Traces tab UI component."""

import gradio as gr
import httpx
import pandas as pd



async def refresh_traces() -> pd.DataFrame:
    """Fetch and display all traces."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://127.0.0.1:8000/api/traces",
                params={"page": 1, "page_size": 50},
            )
            response.raise_for_status()

        data = response.json()
        traces = data.get("traces", [])

        if not traces:
            return pd.DataFrame(columns=[
                "Run ID", "Session", "Events", "Duration", "Tokens", "Cost", "Status", "Time"
            ])

        rows = []
        for trace in traces:
            rows.append({
                "Run ID": trace["run_id"][:8],
                "Session": trace["session_id"][:8] if trace.get("session_id") else "N/A",
                "Events": trace["event_count"],
                "Duration": f"{trace['total_duration_ms']}ms",
                "Tokens": trace["total_tokens"],
                "Cost": f"${trace['total_cost_usd']:.4f}",
                "Status": "✅" if trace["status"] == "success" else "❌",
                "Time": trace["last_event_at"][:19].replace("T", " ") if trace.get("last_event_at") else "N/A",
            })

        return pd.DataFrame(rows)

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})


async def get_trace_details(run_id: str) -> str:
    """Get detailed trace events for a run."""
    if not run_id or not run_id.strip():
        return "Enter a Run ID to view trace details"

    try:
        # Find full run ID
        async with httpx.AsyncClient(timeout=30.0) as client:
            list_response = await client.get(
                "http://127.0.0.1:8000/api/traces",
                params={"page": 1, "page_size": 100},
            )
            list_response.raise_for_status()
            traces = list_response.json().get("traces", [])

            full_id = None
            for trace in traces:
                if trace["run_id"].startswith(run_id.strip()):
                    full_id = trace["run_id"]
                    break

            if not full_id:
                return f"Trace for run '{run_id}' not found"

            # Get details
            response = await client.get(f"http://127.0.0.1:8000/api/traces/{full_id}")
            response.raise_for_status()

        data = response.json()
        events = data.get("events", [])
        summary = data.get("summary", {})

        # Format output
        output = f"""## Trace: `{full_id[:8]}...`

### Summary
| Metric | Value |
|--------|-------|
| Total Events | {summary.get('total_events', 0)} |
| Total Duration | {summary.get('total_duration_ms', 0)}ms |
| Total Tokens | {summary.get('total_tokens', 0)} |
| Total Cost | ${summary.get('total_cost_usd', 0):.4f} |
| Has Errors | {'Yes' if summary.get('has_errors') else 'No'} |

### Event Timeline
"""
        # Event type icons
        type_icons = {
            "retrieval": "🔍",
            "model_call": "🤖",
            "tool_call": "🔧",
            "validation": "✓",
            "error": "❌",
        }

        for event in events:
            icon = type_icons.get(event["event_type"], "•")
            status_marker = "❌" if event["status"] == "error" else ""

            duration = f"{event['duration_ms']}ms" if event.get("duration_ms") else ""
            tokens = ""
            if event.get("tokens_in") or event.get("tokens_out"):
                tokens = f"({event.get('tokens_in', 0)} in / {event.get('tokens_out', 0)} out)"

            output += f"""
---
**{icon} {event['event_name']}** {status_marker}
- Type: `{event['event_type']}`
- Duration: {duration}
- Tokens: {tokens}
- Time: {event['timestamp'][:19].replace('T', ' ')}
"""
            # Add event data summary
            event_data = event.get("event_data", {})
            if event["event_type"] == "retrieval":
                output += f"- Query: *{event_data.get('query', '')[:50]}...*\n"
                output += f"- Results: {event_data.get('results_count', 0)} chunks\n"
            elif event["event_type"] == "model_call":
                output += f"- Model: {event_data.get('model', 'unknown')}\n"

            if event.get("error_message"):
                output += f"- **Error:** {event['error_message']}\n"

        return output

    except httpx.HTTPStatusError as e:
        return f"Failed to load: {e.response.status_code}"
    except Exception as e:
        return f"Failed to load: {str(e)}"


async def delete_trace(run_id: str) -> tuple[str, pd.DataFrame]:
    """Delete trace events for a run."""
    if not run_id or not run_id.strip():
        return "Please enter a Run ID", await refresh_traces()

    try:
        # Find full run ID
        async with httpx.AsyncClient(timeout=30.0) as client:
            list_response = await client.get(
                "http://127.0.0.1:8000/api/traces",
                params={"page": 1, "page_size": 100},
            )
            list_response.raise_for_status()
            traces = list_response.json().get("traces", [])

            full_id = None
            for trace in traces:
                if trace["run_id"].startswith(run_id.strip()):
                    full_id = trace["run_id"]
                    break

            if not full_id:
                return f"Trace '{run_id}' not found", await refresh_traces()

            response = await client.delete(f"http://127.0.0.1:8000/api/traces/{full_id}")
            response.raise_for_status()

        return f"Trace {run_id} deleted", await refresh_traces()

    except httpx.HTTPStatusError as e:
        return f"Delete failed: {e.response.status_code}", await refresh_traces()
    except Exception as e:
        return f"Delete failed: {str(e)}", await refresh_traces()


async def filter_traces(session_id: str, event_type: str) -> pd.DataFrame:
    """Filter traces by session or event type."""
    try:
        params = {"page": 1, "page_size": 50}
        if session_id and session_id.strip():
            params["session_id"] = session_id.strip()
        if event_type and event_type != "All":
            params["event_type"] = event_type.lower()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://127.0.0.1:8000/api/traces",
                params=params,
            )
            response.raise_for_status()

        data = response.json()
        traces = data.get("traces", [])

        if not traces:
            return pd.DataFrame(columns=[
                "Run ID", "Session", "Events", "Duration", "Tokens", "Cost", "Status", "Time"
            ])

        rows = []
        for trace in traces:
            rows.append({
                "Run ID": trace["run_id"][:8],
                "Session": trace["session_id"][:8] if trace.get("session_id") else "N/A",
                "Events": trace["event_count"],
                "Duration": f"{trace['total_duration_ms']}ms",
                "Tokens": trace["total_tokens"],
                "Cost": f"${trace['total_cost_usd']:.4f}",
                "Status": "✅" if trace["status"] == "success" else "❌",
                "Time": trace["last_event_at"][:19].replace("T", " ") if trace.get("last_event_at") else "N/A",
            })

        return pd.DataFrame(rows)

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})


def create_traces_tab() -> gr.Tab:
    """Create the traces tab UI."""
    with gr.Tab("Traces", id="traces") as tab:
        gr.Markdown("## Observability & Tracing")
        gr.Markdown(
            "View detailed traces of every RAG operation: retrievals, model calls, "
            "tool invocations, and validation events."
        )

        with gr.Row():
            # Filters and actions
            with gr.Column(scale=1):
                gr.Markdown("### Filters")

                session_filter = gr.Textbox(
                    label="Session ID",
                    placeholder="Filter by session...",
                )

                event_type_filter = gr.Dropdown(
                    label="Event Type",
                    choices=["All", "Retrieval", "Model_call", "Tool_call", "Validation", "Error"],
                    value="All",
                )

                filter_btn = gr.Button("Apply Filters", variant="secondary")
                clear_filter_btn = gr.Button("Clear Filters", size="sm")

                gr.Markdown("---")
                gr.Markdown("### Actions")

                run_id_input = gr.Textbox(
                    label="Run ID",
                    placeholder="First 8 chars...",
                )

                with gr.Row():
                    view_btn = gr.Button("View Details", size="sm")
                    delete_btn = gr.Button("Delete", variant="stop", size="sm")

                action_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                )

            # Traces list and details
            with gr.Column(scale=2):
                gr.Markdown("### Recent Traces")

                refresh_btn = gr.Button("Refresh", variant="secondary")

                traces_table = gr.DataFrame(
                    label="Traces",
                    interactive=False,
                    wrap=True,
                )

                gr.Markdown("### Trace Details")
                trace_details = gr.Markdown(
                    value="*Select a trace to view event timeline*"
                )

        # Event handlers
        refresh_btn.click(
            fn=refresh_traces,
            outputs=[traces_table],
        )

        filter_btn.click(
            fn=filter_traces,
            inputs=[session_filter, event_type_filter],
            outputs=[traces_table],
        )

        clear_filter_btn.click(
            fn=refresh_traces,
            outputs=[traces_table],
        )

        view_btn.click(
            fn=get_trace_details,
            inputs=[run_id_input],
            outputs=[trace_details],
        )

        delete_btn.click(
            fn=delete_trace,
            inputs=[run_id_input],
            outputs=[action_status, traces_table],
        )

        # Load on tab select
        tab.select(
            fn=refresh_traces,
            outputs=[traces_table],
        )

    return tab
