"""Design system theme for RAGOps Lab UI."""

import gradio as gr

# Design System Tokens
COLORS = {
    "background": "#050505",
    "surface": "#0F0F10",
    "surface_elevated": "#1A1A1B",
    "accent": "#00E676",  # Mint green
    "accent_hover": "#00C853",
    "text_primary": "#EAEAEA",
    "text_secondary": "#9E9E9E",
    "text_muted": "#666666",
    "border": "#2A2A2B",
    "error": "#FF5252",
    "warning": "#FFB300",
    "success": "#00E676",
    "info": "#29B6F6",
}

SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "24px",
    "xxl": "32px",
    "xxxl": "48px",
}

TYPOGRAPHY = {
    "font_family": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "font_mono": "'JetBrains Mono', 'Fira Code', monospace",
    "size_xs": "12px",
    "size_sm": "13px",
    "size_base": "14px",
    "size_lg": "16px",
    "size_xl": "18px",
    "size_xxl": "24px",
}

# Custom CSS for the application
CUSTOM_CSS = f"""
/* Global styles */
body {{
    font-family: {TYPOGRAPHY['font_family']};
    background-color: {COLORS['background']};
    color: {COLORS['text_primary']};
}}

/* Dark theme override */
.dark {{
    --body-background-fill: {COLORS['background']};
    --background-fill-primary: {COLORS['surface']};
    --background-fill-secondary: {COLORS['surface_elevated']};
    --border-color-primary: {COLORS['border']};
    --color-accent: {COLORS['accent']};
}}

/* Headers */
h1, h2, h3 {{
    color: {COLORS['text_primary']};
}}

/* Buttons */
.primary-btn {{
    background-color: {COLORS['accent']} !important;
    color: {COLORS['background']} !important;
    border: none !important;
    font-weight: 600 !important;
}}

.primary-btn:hover {{
    background-color: {COLORS['accent_hover']} !important;
}}

/* Input fields */
.input-field {{
    background-color: {COLORS['surface']} !important;
    border-color: {COLORS['border']} !important;
    color: {COLORS['text_primary']} !important;
}}

/* Cards */
.card {{
    background-color: {COLORS['surface']} !important;
    border: 1px solid {COLORS['border']} !important;
    border-radius: 8px !important;
    padding: {SPACING['lg']} !important;
}}

/* Tables */
.dataframe {{
    background-color: {COLORS['surface']} !important;
}}

.dataframe th {{
    background-color: {COLORS['surface_elevated']} !important;
    color: {COLORS['text_primary']} !important;
}}

.dataframe td {{
    color: {COLORS['text_secondary']} !important;
}}

/* Chatbot */
.chatbot {{
    background-color: {COLORS['surface']} !important;
}}

.message.user {{
    background-color: {COLORS['surface_elevated']} !important;
}}

.message.bot {{
    background-color: {COLORS['surface']} !important;
    border-left: 3px solid {COLORS['accent']} !important;
}}

/* Citations panel */
.citation-item {{
    background-color: {COLORS['surface_elevated']};
    border-left: 3px solid {COLORS['accent']};
    padding: {SPACING['md']};
    margin-bottom: {SPACING['sm']};
    border-radius: 4px;
}}

.citation-source {{
    color: {COLORS['accent']};
    font-weight: 600;
    font-size: {TYPOGRAPHY['size_sm']};
}}

.citation-content {{
    color: {COLORS['text_secondary']};
    font-size: {TYPOGRAPHY['size_sm']};
    margin-top: {SPACING['xs']};
}}

/* Metrics display */
.metric-card {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: {SPACING['lg']};
    text-align: center;
}}

.metric-value {{
    font-size: {TYPOGRAPHY['size_xxl']};
    font-weight: 700;
    color: {COLORS['accent']};
}}

.metric-label {{
    font-size: {TYPOGRAPHY['size_sm']};
    color: {COLORS['text_secondary']};
    margin-top: {SPACING['xs']};
}}

/* Timeline for traces */
.trace-event {{
    display: flex;
    align-items: flex-start;
    padding: {SPACING['md']};
    border-left: 2px solid {COLORS['border']};
    margin-left: {SPACING['md']};
}}

.trace-event.retrieval {{
    border-left-color: {COLORS['info']};
}}

.trace-event.model_call {{
    border-left-color: {COLORS['accent']};
}}

.trace-event.error {{
    border-left-color: {COLORS['error']};
}}

/* Status badges */
.status-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: {TYPOGRAPHY['size_xs']};
    font-weight: 600;
    text-transform: uppercase;
}}

.status-success {{
    background-color: rgba(0, 230, 118, 0.2);
    color: {COLORS['success']};
}}

.status-error {{
    background-color: rgba(255, 82, 82, 0.2);
    color: {COLORS['error']};
}}

.status-pending {{
    background-color: rgba(255, 179, 0, 0.2);
    color: {COLORS['warning']};
}}

/* Code blocks */
pre, code {{
    font-family: {TYPOGRAPHY['font_mono']};
    background-color: {COLORS['surface_elevated']} !important;
    border-radius: 4px;
}}

/* Scrollbar styling */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: {COLORS['surface']};
}}

::-webkit-scrollbar-thumb {{
    background: {COLORS['border']};
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: {COLORS['text_muted']};
}}

/* Tab styling */
.tab-nav {{
    background-color: {COLORS['surface']} !important;
    border-bottom: 1px solid {COLORS['border']} !important;
}}

.tab-nav button {{
    color: {COLORS['text_secondary']} !important;
}}

.tab-nav button.selected {{
    color: {COLORS['accent']} !important;
    border-bottom: 2px solid {COLORS['accent']} !important;
}}
"""


def create_theme() -> gr.Theme:
    """Create the custom Gradio theme."""
    return gr.themes.Base(
        primary_hue=gr.themes.colors.emerald,
        secondary_hue=gr.themes.colors.gray,
        neutral_hue=gr.themes.colors.gray,
        font=gr.themes.GoogleFont("Inter"),
        font_mono=gr.themes.GoogleFont("JetBrains Mono"),
    ).set(
        body_background_fill=COLORS["background"],
        body_background_fill_dark=COLORS["background"],
        block_background_fill=COLORS["surface"],
        block_background_fill_dark=COLORS["surface"],
        block_border_color=COLORS["border"],
        block_border_color_dark=COLORS["border"],
        button_primary_background_fill=COLORS["accent"],
        button_primary_background_fill_dark=COLORS["accent"],
        button_primary_text_color=COLORS["background"],
        button_primary_text_color_dark=COLORS["background"],
        input_background_fill=COLORS["surface"],
        input_background_fill_dark=COLORS["surface"],
        input_border_color=COLORS["border"],
        input_border_color_dark=COLORS["border"],
    )
