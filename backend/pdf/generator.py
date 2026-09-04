import uuid
import logging
from pathlib import Path
from jinja2 import Template
from playwright.async_api import async_playwright
from config import settings
from pdf.templates import TEMPLATES, MODERN_TEMPLATE

logger = logging.getLogger("resume_rag.pdf")

class PDFGenerator:
    def __init__(self, output_dir: Path = settings.PDF_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_html(self, resume_data: dict, template_name: str = "modern") -> str:
        template_str = TEMPLATES.get(template_name.lower(), MODERN_TEMPLATE)
        jinja_template = Template(template_str)
        return jinja_template.render(**resume_data)

    async def generate_pdf(self, resume_data: dict, template_name: str = "modern") -> Path:
        html_content = self.render_html(resume_data, template_name)
        
        filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
        output_path = self.output_dir / filename

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set HTML content and wait for network/fonts
            await page.set_content(html_content, wait_until="networkidle")
            
            # Print to PDF with exact A4 sizing
            await page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"}
            )
            await browser.close()

        logger.info(f"Generated PDF successfully at {output_path}")
        return output_path

pdf_generator = PDFGenerator()
