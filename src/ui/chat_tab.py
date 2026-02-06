"""Chat tab UI component."""

import uuid
from typing import Optional

import gradio as gr
import httpx


def format_citations(citations: list) -> str:
    """Format citations for display."""
    if not citations:
        return "*No sources used*"

    html_parts = []
    for i, citation in enumerate(citations, 1):
        doc_name = citation.get("document_name", "Unknown")
        page = citation.get("page_number")
        score = citation.get("relevance_score", 0)
        content = citation.get("content", "")[:200]

        page_info = f" (Page {page})" if page else ""
        score_pct = f"{score * 100:.0f}%"

        html_parts.append(f"""
**[{i}] {doc_name}{page_info}** - Relevance: {score_pct}

> {content}...

---
""")

    return "\n".join(html_parts)


async def send_message(
    message: str,
    history: list,
    session_id: Optional[str],
) -> tuple[list, str, str, str]:
    """Send a chat message and get response."""
    if not message.strip():
        return history, "", session_id or "", ""

    # Generate session ID if needed
    if not session_id:
        session_id = str(uuid.uuid4())

    # Add user message to history (Gradio 6.0 format)
    history = history + [{"role": "user", "content": message}]

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "/api/chat",
                json={
                    "message": message,
                    "session_id": session_id,
                    "include_sources": True,
                    "max_sources": 5,
                },
            )
            response.raise_for_status()
            data = response.json()

        # Extract response data
        assistant_message = data["message"]["content"]
        citations = data["message"].get("citations", [])
        is_refusal = data["message"].get("is_refusal", False)

        # Add assistant message to history (Gradio 6.0 format)
        history = history + [{"role": "assistant", "content": assistant_message}]

        # Format citations
        citations_display = format_citations(citations)

        # Format metadata
        latency = data.get("latency_ms", 0)
        tokens = data.get("tokens_used", "N/A")
        run_id = data.get("run_id", "")

        metadata = f"**Run ID:** `{run_id}`\n**Latency:** {latency}ms\n**Tokens:** {tokens}"
        if is_refusal:
            metadata += "\n\n**Status:** Refusal (insufficient context)"

        return history, "", session_id, citations_display

    except httpx.HTTPStatusError as e:
        error_msg = f"Error: {e.response.status_code} - {e.response.text}"
        history = history + [{"role": "assistant", "content": error_msg}]
        return history, "", session_id or "", ""
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        history = history + [{"role": "assistant", "content": error_msg}]
        return history, "", session_id or "", ""


def clear_chat():
    """Clear chat history and start new session."""
    return [], "", str(uuid.uuid4()), ""


def create_chat_tab() -> gr.Tab:
    """Create the chat tab UI."""
    with gr.Tab("Chat", id="chat") as tab:
        gr.Markdown("## Chat with Your Documents")
        gr.Markdown(
            "Ask questions about your uploaded documents. "
            "All responses include citations to source material."
        )

        with gr.Row():
            # Main chat area
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=500,
                )

                with gr.Row():
                    message_input = gr.Textbox(
                        label="Your Question",
                        placeholder="Ask a question about your documents...",
                        scale=4,
                        show_label=False,
                    )
                    send_btn = gr.Button(
                        "Send",
                        variant="primary",
                        scale=1,
                    )

                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", variant="secondary")
                    session_display = gr.Textbox(
                        label="Session ID",
                        interactive=False,
                        scale=2,
                    )

            # Citations sidebar
            with gr.Column(scale=1):
                gr.Markdown("### Sources")
                citations_display = gr.Markdown(
                    value="*Send a message to see sources*",
                    label="Citations",
                )

        # Hidden state
        session_state = gr.State(value=None)

        # Event handlers
        send_btn.click(
            fn=send_message,
            inputs=[message_input, chatbot, session_state],
            outputs=[chatbot, message_input, session_display, citations_display],
        )

        message_input.submit(
            fn=send_message,
            inputs=[message_input, chatbot, session_state],
            outputs=[chatbot, message_input, session_display, citations_display],
        )

        clear_btn.click(
            fn=clear_chat,
            outputs=[chatbot, message_input, session_display, citations_display],
        )

    return tab
