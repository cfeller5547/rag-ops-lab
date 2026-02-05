"""Main Gradio application for RAGOps Lab."""

import gradio as gr

from src.ui.chat_tab import create_chat_tab
from src.ui.corpus_tab import create_corpus_tab
from src.ui.evals_tab import create_evals_tab
from src.ui.settings_tab import create_settings_tab
from src.ui.traces_tab import create_traces_tab


def create_gradio_app() -> gr.Blocks:
    """Create the main Gradio application."""
    with gr.Blocks(
        title="RAGOps Lab",
    ) as app:
        # Header
        gr.Markdown(
            """
# RAGOps Lab

**Agentic RAG + Evaluation + Observability Platform**

Upload documents, chat with citations, run evaluations, and trace every operation.
            """,
            elem_classes=["header"],
        )

        # Main tabs
        with gr.Tabs():
            create_chat_tab()
            create_corpus_tab()
            create_evals_tab()
            create_traces_tab()
            create_settings_tab()

        # Footer
        gr.Markdown(
            """
---
<center>

**RAGOps Lab** v0.1.0 | [API Docs](/docs) | [Health](/health)

</center>
            """,
            elem_classes=["footer"],
        )

    return app
