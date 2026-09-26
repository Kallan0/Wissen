import uuid
import asyncio
import logging
from pathlib import Path
from jinja2 import Environment, select_autoescape
from config import settings
from pdf.templates import TEMPLATES, MODERN_TEMPLATE

logger = logging.getLogger("resume_rag.pdf")

_template_environment = Environment(
    autoescape=select_autoescape(default_for_string=True, default=True),
)


class PDFGenerator:
    def __init__(self, output_dir: Path = settings.PDF_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_html(self, resume_data: dict, template_name: str = "modern") -> str:
        template_str = TEMPLATES.get(template_name.lower(), MODERN_TEMPLATE)
        jinja_template = _template_environment.from_string(template_str)
        return jinja_template.render(**resume_data)

    def _generate_pdf_sync(self, html_content: str, output_path: Path) -> None:
        """
        Runs Playwright synchronously.  Called inside a threadpool executor so
        the FastAPI event loop stays unblocked.  Using sync_playwright avoids
        the Windows SelectorEventLoop limitation where asyncio cannot spawn
        subprocesses (NotImplementedError from asyncio.create_subprocess_exec).
        """
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Wait for network/fonts to settle (e.g. Google Fonts in vintage template)
            page.set_content(html_content, wait_until="networkidle")
            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"},
            )
            browser.close()

    async def generate_pdf(self, resume_data: dict, template_name: str = "modern") -> Path:
        """
        Async entry point.  Renders the HTML template, then offloads the
        Playwright/Chromium work to a thread so the event loop is never blocked.
        """
        html_content = self.render_html(resume_data, template_name)
        filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
        output_path = self.output_dir / filename

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._generate_pdf_sync, html_content, output_path)

        logger.info(f"Generated PDF successfully at {output_path}")
        return output_path


pdf_generator = PDFGenerator()
