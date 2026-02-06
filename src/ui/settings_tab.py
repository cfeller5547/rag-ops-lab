"""Settings tab UI component."""

import gradio as gr
import httpx

from src.config import get_settings


def get_current_settings() -> dict:
    """Get current application settings."""
    settings = get_settings()
    return {
        "openai_model": settings.openai_model,
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "top_k_retrieval": settings.top_k_retrieval,
        "eval_batch_size": settings.eval_batch_size,
        "log_level": settings.log_level,
    }


async def check_api_health() -> str:
    """Check API health status."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("/health")
            response.raise_for_status()

        data = response.json()
        return f"""### System Status

| Component | Status |
|-----------|--------|
| API Server | ✅ Online |
| Database | ✅ {data.get('database', 'Connected')} |
| Vector Store | ✅ {data.get('vector_store', 'Connected')} |

**Version:** {data.get('version', '0.1.0')}
"""
    except Exception as e:
        return f"""### System Status

| Component | Status |
|-----------|--------|
| API Server | ❌ Offline |
| Error | {str(e)} |
"""


async def get_system_info() -> str:
    """Get system information and statistics."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get document stats
            docs_response = await client.get(
                "/api/documents",
                params={"page": 1, "page_size": 1000},
            )
            docs_data = docs_response.json()

            # Get trace stats
            traces_response = await client.get(
                "/api/traces",
                params={"page": 1, "page_size": 1000},
            )
            traces_data = traces_response.json()

            # Get eval stats
            evals_response = await client.get(
                "/api/evals",
                params={"page": 1, "page_size": 1000},
            )
            evals_data = evals_response.json()

        docs = docs_data.get("documents", [])
        total_chunks = sum(d.get("chunk_count", 0) for d in docs)
        total_size = sum(d.get("file_size", 0) for d in docs)

        traces = traces_data.get("traces", [])
        total_cost = sum(t.get("total_cost_usd", 0) for t in traces)

        return f"""### Usage Statistics

**Documents**
- Total: {docs_data.get('total', 0)}
- Chunks: {total_chunks}
- Storage: {total_size / (1024 * 1024):.2f} MB

**Evaluations**
- Total Runs: {evals_data.get('total', 0)}

**Traces**
- Total: {traces_data.get('total', 0)}
- Est. Cost: ${total_cost:.4f}
"""
    except Exception as e:
        return f"Failed to load statistics: {str(e)}"


def load_settings_display() -> tuple:
    """Load current settings for display."""
    settings = get_current_settings()
    return (
        settings["openai_model"],
        settings["embedding_model"],
        settings["chunk_size"],
        settings["chunk_overlap"],
        settings["top_k_retrieval"],
    )


def create_settings_tab() -> gr.Tab:
    """Create the settings tab UI."""
    with gr.Tab("Settings", id="settings") as tab:
        gr.Markdown("## Settings & Configuration")
        gr.Markdown(
            "View and manage system settings. Note: Some settings require a restart to take effect."
        )

        with gr.Row():
            # Settings panel
            with gr.Column(scale=1):
                gr.Markdown("### Model Configuration")

                model_dropdown = gr.Dropdown(
                    label="LLM Model",
                    choices=[
                        "gpt-4-turbo-preview",
                        "gpt-4",
                        "gpt-4o",
                        "gpt-4o-mini",
                        "gpt-3.5-turbo",
                    ],
                    value="gpt-4-turbo-preview",
                    interactive=False,  # Read-only for now
                    info="Configured via environment variable",
                )

                embedding_dropdown = gr.Dropdown(
                    label="Embedding Model",
                    choices=[
                        "text-embedding-3-small",
                        "text-embedding-3-large",
                    ],
                    value="text-embedding-3-small",
                    interactive=False,
                    info="Configured via environment variable",
                )

                gr.Markdown("### Retrieval Settings")

                chunk_size = gr.Number(
                    label="Chunk Size",
                    value=512,
                    interactive=False,
                    info="Characters per chunk",
                )

                chunk_overlap = gr.Number(
                    label="Chunk Overlap",
                    value=50,
                    interactive=False,
                    info="Overlap between chunks",
                )

                top_k = gr.Number(
                    label="Top-K Retrieval",
                    value=5,
                    interactive=False,
                    info="Number of chunks to retrieve",
                )

                gr.Markdown("---")

                gr.Markdown("""
### Configuration

Settings are managed via environment variables.
Edit `.env` file or set environment variables:

```
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5
```

Restart the application after changing settings.
""")

            # Status and info panel
            with gr.Column(scale=1):
                gr.Markdown("### System Health")

                health_display = gr.Markdown(value="*Loading...*")
                health_btn = gr.Button("Check Health", variant="secondary")

                gr.Markdown("---")

                stats_display = gr.Markdown(value="*Loading...*")
                stats_btn = gr.Button("Refresh Stats", variant="secondary")

                gr.Markdown("---")

                gr.Markdown("""
### Quick Links

- [API Documentation](/docs) - Interactive API docs
- [Health Check](/health) - System health endpoint
- [GitHub](https://github.com/yourusername/rag-ops-lab) - Source code

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Send Message | Enter |
| Clear Chat | Ctrl+L |
| Focus Input | / |
""")

        # Event handlers
        health_btn.click(
            fn=check_api_health,
            outputs=[health_display],
        )

        stats_btn.click(
            fn=get_system_info,
            outputs=[stats_display],
        )

        # Load on tab select
        tab.select(
            fn=check_api_health,
            outputs=[health_display],
        )
        tab.select(
            fn=get_system_info,
            outputs=[stats_display],
        )
        tab.select(
            fn=load_settings_display,
            outputs=[model_dropdown, embedding_dropdown, chunk_size, chunk_overlap, top_k],
        )

    return tab
