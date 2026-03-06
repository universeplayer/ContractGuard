"""Gradio web UI for ContractGuard."""

from __future__ import annotations

import tempfile
from pathlib import Path

import gradio as gr

from contractguard.analyzer import analyze_contract, DEFAULT_MODEL
from contractguard.parser import extract_text
from contractguard.report import generate_markdown_report


def _analyze(file, model: str, api_key: str) -> tuple[str, str, str]:
    """Run analysis and return (summary, report_md, score)."""
    if file is None:
        return "", "Please upload a contract file.", ""

    try:
        text = extract_text(file.name)
    except Exception as e:
        return "", f"**Error parsing file:** {e}", ""

    kwargs = {"contract_text": text, "model": model or DEFAULT_MODEL}
    if api_key:
        kwargs["api_key"] = api_key

    try:
        result = analyze_contract(**kwargs)
    except Exception as e:
        return "", f"**Error during analysis:** {e}", ""

    grade_emoji = {
        "A+": "🟢", "A": "🟢", "B+": "🟡", "B": "🟡",
        "C+": "🟠", "C": "🟠", "D": "🔴", "F": "🔴",
    }
    emoji = grade_emoji.get(result.fairness_grade, "⚪")
    score_text = f"{emoji} **{result.fairness_grade}** ({result.fairness_score}/100)"

    summary = (
        f"**Contract type:** {result.contract_type.value.replace('_', ' ').title()}\n\n"
        f"**Parties:** {', '.join(result.parties)}\n\n"
        f"{result.summary}"
    )

    report = generate_markdown_report(result)
    return summary, report, score_text


def create_app() -> gr.Blocks:
    with gr.Blocks(
        title="ContractGuard",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown(
            "# ContractGuard\n"
            "Upload a contract (PDF, DOCX, or TXT) and get an instant AI review "
            "with red flags, warnings, and a fairness score."
        )

        with gr.Row():
            with gr.Column(scale=1):
                file_input = gr.File(
                    label="Upload Contract",
                    file_types=[".pdf", ".docx", ".txt", ".md"],
                )
                model_input = gr.Textbox(
                    label="Model",
                    value=DEFAULT_MODEL,
                    placeholder="e.g. openai/gpt-4o",
                )
                api_key_input = gr.Textbox(
                    label="API Key (or set OPENROUTER_API_KEY env var)",
                    type="password",
                    placeholder="sk-or-...",
                )
                scan_btn = gr.Button("Scan Contract", variant="primary")

            with gr.Column(scale=2):
                score_output = gr.Markdown(label="Fairness Score")
                summary_output = gr.Markdown(label="Summary")

        report_output = gr.Markdown(label="Full Report")

        scan_btn.click(
            fn=_analyze,
            inputs=[file_input, model_input, api_key_input],
            outputs=[summary_output, report_output, score_output],
        )

    return app


def main():
    app = create_app()
    app.launch()


if __name__ == "__main__":
    main()
