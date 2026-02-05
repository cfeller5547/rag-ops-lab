"""Evaluations tab UI component."""

import gradio as gr
import httpx
import pandas as pd


async def list_datasets() -> list:
    """Fetch available evaluation datasets."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:8000/api/evals/datasets")
            response.raise_for_status()

        datasets = response.json()
        return [d["name"] for d in datasets]
    except Exception:
        return ["default_50"]


async def refresh_eval_runs() -> pd.DataFrame:
    """Fetch and display all evaluation runs."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://localhost:8000/api/evals",
                params={"page": 1, "page_size": 50},
            )
            response.raise_for_status()

        data = response.json()
        eval_runs = data.get("eval_runs", [])

        if not eval_runs:
            return pd.DataFrame(columns=[
                "ID", "Name", "Dataset", "Progress", "Status",
                "Groundedness", "Hallucination", "Latency P95", "Created"
            ])

        rows = []
        for run in eval_runs:
            metrics = run.get("metrics") or {}
            progress = f"{run['completed_cases']}/{run['total_cases']}"

            rows.append({
                "ID": run["eval_id"][:8],
                "Name": run["name"],
                "Dataset": run["dataset_name"],
                "Progress": progress,
                "Status": run["status"].capitalize(),
                "Groundedness": f"{metrics.get('groundedness_score', 0) * 100:.1f}%" if metrics else "N/A",
                "Hallucination": f"{metrics.get('hallucination_rate', 0) * 100:.1f}%" if metrics else "N/A",
                "Latency P95": f"{metrics.get('latency_p95_ms', 0):.0f}ms" if metrics else "N/A",
                "Created": run["created_at"][:19].replace("T", " "),
            })

        return pd.DataFrame(rows)

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})


async def start_eval_run(name: str, dataset: str) -> tuple[str, pd.DataFrame]:
    """Start a new evaluation run."""
    if not name or not name.strip():
        return "Please enter a name for the evaluation", await refresh_eval_runs()

    if not dataset:
        return "Please select a dataset", await refresh_eval_runs()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/evals",
                json={
                    "name": name.strip(),
                    "dataset_name": dataset,
                },
            )
            response.raise_for_status()

        data = response.json()
        return f"Evaluation started: {data['eval_id'][:8]}", await refresh_eval_runs()

    except httpx.HTTPStatusError as e:
        return f"Failed: {e.response.status_code} - {e.response.text}", await refresh_eval_runs()
    except Exception as e:
        return f"Failed: {str(e)}", await refresh_eval_runs()


async def get_eval_details(eval_id: str) -> str:
    """Get detailed results for an evaluation run."""
    if not eval_id or not eval_id.strip():
        return "Enter an evaluation ID to view details"

    try:
        # Expand short ID to full if needed
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First get list to find full ID
            list_response = await client.get(
                "http://localhost:8000/api/evals",
                params={"page": 1, "page_size": 100},
            )
            list_response.raise_for_status()
            runs = list_response.json().get("eval_runs", [])

            full_id = None
            for run in runs:
                if run["eval_id"].startswith(eval_id.strip()):
                    full_id = run["eval_id"]
                    break

            if not full_id:
                return f"Evaluation '{eval_id}' not found"

            # Get details
            response = await client.get(f"http://localhost:8000/api/evals/{full_id}")
            response.raise_for_status()

        data = response.json()

        # Format details
        metrics = data.get("metrics") or {}
        results = data.get("results", [])

        output = f"""## Evaluation: {data['name']}

**ID:** `{data['eval_id']}`
**Dataset:** {data['dataset_name']}
**Status:** {data['status'].capitalize()}
**Progress:** {data['completed_cases']}/{data['total_cases']} cases

### Metrics
| Metric | Value |
|--------|-------|
| Groundedness | {metrics.get('groundedness_score', 0) * 100:.1f}% |
| Hallucination Rate | {metrics.get('hallucination_rate', 0) * 100:.1f}% |
| Schema Compliance | {metrics.get('schema_compliance', 0) * 100:.1f}% |
| Tool Correctness | {metrics.get('tool_correctness', 0) * 100:.1f}% |
| Latency P95 | {metrics.get('latency_p95_ms', 0):.0f}ms |

### Sample Results
"""
        # Add sample results
        for result in results[:5]:
            status_emoji = "✅" if result["status"] == "passed" else "❌"
            output += f"""
---
**{status_emoji} Case: {result['case_id']}**
- Question: {result['question'][:100]}...
- Status: {result['status']}
- Groundedness: {result.get('groundedness_score', 0) * 100:.1f}%
- Latency: {result.get('latency_ms', 0)}ms
"""
        if len(results) > 5:
            output += f"\n*...and {len(results) - 5} more results*"

        return output

    except httpx.HTTPStatusError as e:
        return f"Failed to load: {e.response.status_code}"
    except Exception as e:
        return f"Failed to load: {str(e)}"


async def delete_eval_run(eval_id: str) -> tuple[str, pd.DataFrame]:
    """Delete an evaluation run."""
    if not eval_id or not eval_id.strip():
        return "Please enter an evaluation ID", await refresh_eval_runs()

    try:
        # Find full ID
        async with httpx.AsyncClient(timeout=30.0) as client:
            list_response = await client.get(
                "http://localhost:8000/api/evals",
                params={"page": 1, "page_size": 100},
            )
            list_response.raise_for_status()
            runs = list_response.json().get("eval_runs", [])

            full_id = None
            for run in runs:
                if run["eval_id"].startswith(eval_id.strip()):
                    full_id = run["eval_id"]
                    break

            if not full_id:
                return f"Evaluation '{eval_id}' not found", await refresh_eval_runs()

            response = await client.delete(f"http://localhost:8000/api/evals/{full_id}")
            response.raise_for_status()

        return f"Evaluation {eval_id} deleted", await refresh_eval_runs()

    except httpx.HTTPStatusError as e:
        return f"Delete failed: {e.response.status_code}", await refresh_eval_runs()
    except Exception as e:
        return f"Delete failed: {str(e)}", await refresh_eval_runs()


def create_evals_tab() -> gr.Tab:
    """Create the evaluations tab UI."""
    with gr.Tab("Evaluations", id="evals") as tab:
        gr.Markdown("## Evaluation Harness")
        gr.Markdown(
            "Run evaluations against your RAG system to measure quality metrics: "
            "groundedness, hallucination rate, schema compliance, tool correctness, and latency."
        )

        with gr.Row():
            # New evaluation
            with gr.Column(scale=1):
                gr.Markdown("### Start New Evaluation")

                eval_name = gr.Textbox(
                    label="Evaluation Name",
                    placeholder="e.g., baseline_v1",
                )

                dataset_dropdown = gr.Dropdown(
                    label="Dataset",
                    choices=["default_50"],
                    value="default_50",
                )

                start_btn = gr.Button("Start Evaluation", variant="primary")
                start_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                )

                gr.Markdown("---")
                gr.Markdown("### Quick Actions")

                with gr.Row():
                    eval_id_input = gr.Textbox(
                        label="Eval ID",
                        placeholder="First 8 chars...",
                        scale=2,
                    )
                with gr.Row():
                    view_btn = gr.Button("View Details", size="sm")
                    delete_btn = gr.Button("Delete", variant="stop", size="sm")

            # Evaluation list and details
            with gr.Column(scale=2):
                gr.Markdown("### Evaluation Runs")

                refresh_btn = gr.Button("Refresh", variant="secondary")

                evals_table = gr.DataFrame(
                    label="Evaluations",
                    interactive=False,
                    wrap=True,
                )

                gr.Markdown("### Details")
                eval_details = gr.Markdown(
                    value="*Select an evaluation to view details*"
                )

        # Event handlers
        start_btn.click(
            fn=start_eval_run,
            inputs=[eval_name, dataset_dropdown],
            outputs=[start_status, evals_table],
        )

        refresh_btn.click(
            fn=refresh_eval_runs,
            outputs=[evals_table],
        )

        view_btn.click(
            fn=get_eval_details,
            inputs=[eval_id_input],
            outputs=[eval_details],
        )

        delete_btn.click(
            fn=delete_eval_run,
            inputs=[eval_id_input],
            outputs=[start_status, evals_table],
        )

        # Load on tab select
        tab.select(
            fn=refresh_eval_runs,
            outputs=[evals_table],
        )

    return tab
