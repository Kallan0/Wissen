from pdf.generator import PDFGenerator


def _resume(summary: str = "Verified backend developer") -> dict:
    return {
        "name": "Joji George Alungal",
        "title": "Python Backend Developer",
        "contact": {},
        "summary": summary,
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
    }


def test_all_resume_templates_are_rendered_by_backend(tmp_path):
    generator = PDFGenerator(output_dir=tmp_path)

    for template in ("modern", "minimal", "vintage"):
        html = generator.render_html(_resume(), template)
        assert "Joji George Alungal" in html
        assert "Verified backend developer" in html
        assert html.lstrip().startswith("<!DOCTYPE html>")


def test_resume_values_are_html_escaped(tmp_path):
    generator = PDFGenerator(output_dir=tmp_path)
    html = generator.render_html(_resume('<script>alert("unsafe")</script>'), "modern")

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
