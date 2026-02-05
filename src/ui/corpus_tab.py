"""Corpus management tab UI component."""

import gradio as gr
import httpx
import pandas as pd
from pathlib import Path


async def upload_document(file) -> str:
    """Upload a document to the API."""
    if file is None:
        return "No file selected"

    try:
        file_path = Path(file.name)
        content_type = "application/pdf" if file_path.suffix == ".pdf" else "text/plain"

        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(file.name, "rb") as f:
                files = {"file": (file_path.name, f, content_type)}
                response = await client.post(
                    "http://localhost:8000/api/documents",
                    files=files,
                )
                response.raise_for_status()

        data = response.json()
        return f"Uploaded: {data['original_filename']} (Status: {data['status']}, Chunks: {data['chunk_count']})"

    except httpx.HTTPStatusError as e:
        return f"Upload failed: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Upload failed: {str(e)}"


async def refresh_documents() -> pd.DataFrame:
    """Fetch and display all documents."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://localhost:8000/api/documents",
                params={"page": 1, "page_size": 100},
            )
            response.raise_for_status()

        data = response.json()
        documents = data.get("documents", [])

        if not documents:
            return pd.DataFrame(columns=["ID", "Filename", "Type", "Size", "Chunks", "Status", "Created"])

        rows = []
        for doc in documents:
            rows.append({
                "ID": doc["id"],
                "Filename": doc["original_filename"],
                "Type": doc["content_type"].split("/")[-1].upper(),
                "Size": f"{doc['file_size'] / 1024:.1f} KB",
                "Chunks": doc["chunk_count"],
                "Status": doc["status"].capitalize(),
                "Created": doc["created_at"][:19].replace("T", " "),
            })

        return pd.DataFrame(rows)

    except Exception as e:
        return pd.DataFrame({
            "Error": [str(e)]
        })


async def delete_document(doc_id: str) -> tuple[str, pd.DataFrame]:
    """Delete a document by ID."""
    if not doc_id or not doc_id.strip():
        return "Please enter a document ID", await refresh_documents()

    try:
        doc_id_int = int(doc_id.strip())
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"http://localhost:8000/api/documents/{doc_id_int}"
            )
            response.raise_for_status()

        return f"Document {doc_id_int} deleted successfully", await refresh_documents()

    except ValueError:
        return "Invalid document ID", await refresh_documents()
    except httpx.HTTPStatusError as e:
        return f"Delete failed: {e.response.status_code}", await refresh_documents()
    except Exception as e:
        return f"Delete failed: {str(e)}", await refresh_documents()


async def reprocess_document(doc_id: str) -> tuple[str, pd.DataFrame]:
    """Reprocess a document by ID."""
    if not doc_id or not doc_id.strip():
        return "Please enter a document ID", await refresh_documents()

    try:
        doc_id_int = int(doc_id.strip())
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"http://localhost:8000/api/documents/{doc_id_int}/reprocess"
            )
            response.raise_for_status()

        data = response.json()
        return f"Document {doc_id_int} reprocessed (Status: {data['status']})", await refresh_documents()

    except ValueError:
        return "Invalid document ID", await refresh_documents()
    except httpx.HTTPStatusError as e:
        return f"Reprocess failed: {e.response.status_code}", await refresh_documents()
    except Exception as e:
        return f"Reprocess failed: {str(e)}", await refresh_documents()


async def get_corpus_stats() -> str:
    """Get corpus statistics."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://localhost:8000/api/documents",
                params={"page": 1, "page_size": 1000},
            )
            response.raise_for_status()

        data = response.json()
        total_docs = data.get("total", 0)
        documents = data.get("documents", [])

        total_chunks = sum(doc.get("chunk_count", 0) for doc in documents)
        total_size = sum(doc.get("file_size", 0) for doc in documents)
        completed = sum(1 for doc in documents if doc.get("status") == "completed")
        failed = sum(1 for doc in documents if doc.get("status") == "failed")

        return f"""### Corpus Statistics

- **Total Documents:** {total_docs}
- **Completed:** {completed}
- **Failed:** {failed}
- **Total Chunks:** {total_chunks}
- **Total Size:** {total_size / (1024 * 1024):.2f} MB
"""
    except Exception as e:
        return f"Failed to load stats: {str(e)}"


def create_corpus_tab() -> gr.Tab:
    """Create the corpus management tab UI."""
    with gr.Tab("Corpus", id="corpus") as tab:
        gr.Markdown("## Document Corpus Management")
        gr.Markdown(
            "Upload, view, and manage your document corpus. "
            "Supported formats: PDF, TXT, Markdown."
        )

        with gr.Row():
            # Upload section
            with gr.Column(scale=1):
                gr.Markdown("### Upload Document")
                file_upload = gr.File(
                    label="Select File",
                    file_types=[".pdf", ".txt", ".md"],
                )
                upload_btn = gr.Button("Upload", variant="primary")
                upload_status = gr.Textbox(
                    label="Upload Status",
                    interactive=False,
                )

                gr.Markdown("---")

                # Stats
                stats_display = gr.Markdown(
                    value="Loading...",
                    label="Statistics",
                )
                refresh_stats_btn = gr.Button("Refresh Stats", size="sm")

            # Document list
            with gr.Column(scale=2):
                gr.Markdown("### Documents")

                with gr.Row():
                    refresh_btn = gr.Button("Refresh List", variant="secondary")

                documents_table = gr.DataFrame(
                    label="Documents",
                    interactive=False,
                    wrap=True,
                )

                gr.Markdown("### Document Actions")
                with gr.Row():
                    doc_id_input = gr.Textbox(
                        label="Document ID",
                        placeholder="Enter document ID...",
                        scale=2,
                    )
                    delete_btn = gr.Button("Delete", variant="stop", scale=1)
                    reprocess_btn = gr.Button("Reprocess", variant="secondary", scale=1)

                action_status = gr.Textbox(
                    label="Action Status",
                    interactive=False,
                )

        # Event handlers
        upload_btn.click(
            fn=upload_document,
            inputs=[file_upload],
            outputs=[upload_status],
        ).then(
            fn=refresh_documents,
            outputs=[documents_table],
        ).then(
            fn=get_corpus_stats,
            outputs=[stats_display],
        )

        refresh_btn.click(
            fn=refresh_documents,
            outputs=[documents_table],
        )

        refresh_stats_btn.click(
            fn=get_corpus_stats,
            outputs=[stats_display],
        )

        delete_btn.click(
            fn=delete_document,
            inputs=[doc_id_input],
            outputs=[action_status, documents_table],
        ).then(
            fn=get_corpus_stats,
            outputs=[stats_display],
        )

        reprocess_btn.click(
            fn=reprocess_document,
            inputs=[doc_id_input],
            outputs=[action_status, documents_table],
        )

        # Initial load
        tab.select(
            fn=refresh_documents,
            outputs=[documents_table],
        )
        tab.select(
            fn=get_corpus_stats,
            outputs=[stats_display],
        )

    return tab
