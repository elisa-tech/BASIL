from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import Response
import os
import tempfile
import subprocess
from typing import Optional

app = FastAPI()

# Define request body schema
class ConvertRequest(BaseModel):
    html: str  # HTML content
    margin_top_mm: Optional[int] = None
    margin_bottom_mm: Optional[int] = None
    margin_left_mm: Optional[int] = None
    margin_right_mm: Optional[int] = None
    page_size: Optional[str] = None
    footer_center: Optional[str] = None
    footer_left: Optional[str] = None
    footer_right: Optional[str] = None
    footer_font_size: Optional[int] = None
    footer_spacing_mm: Optional[int] = None
    footer_line: Optional[bool] = None

# Set TMPDIR in Python
os.environ["TMPDIR"] = "/tmp/workdir"

# Copy current environment and pass it to subprocess
env = os.environ.copy()

@app.post("/convert")
async def convert_to_pdf(req: ConvertRequest):
    html_content = req.html

    html_file = tempfile.NamedTemporaryFile(dir="/tmp/workdir", suffix=".html", delete=False)
    pdf_file = tempfile.NamedTemporaryFile(dir="/tmp/workdir", suffix=".pdf", delete=False)

    html_path = html_file.name
    pdf_path = pdf_file.name

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    def _fmt_margin(mm: Optional[int], default_value: str) -> str:
        try:
            return f"{int(mm)}mm" if mm is not None else default_value
        except Exception:
            return default_value

    margin_top = _fmt_margin(req.margin_top_mm, "10mm")
    margin_bottom = _fmt_margin(req.margin_bottom_mm, "10mm")
    margin_left = _fmt_margin(req.margin_left_mm, "10mm")
    margin_right = _fmt_margin(req.margin_right_mm, "10mm")
    page_size = req.page_size or "A4"

    pandoc_args = [
        "pandoc", html_path,
        "-o", pdf_path,
        "--pdf-engine=wkhtmltopdf",
        "--pdf-engine-opt=--enable-local-file-access",
        "--pdf-engine-opt=--print-media-type",
        "--pdf-engine-opt=--background",
        "--pdf-engine-opt=--margin-top", f"--pdf-engine-opt={margin_top}",
        "--pdf-engine-opt=--margin-bottom", f"--pdf-engine-opt={margin_bottom}",
        "--pdf-engine-opt=--margin-left", f"--pdf-engine-opt={margin_left}",
        "--pdf-engine-opt=--margin-right", f"--pdf-engine-opt={margin_right}",
        "--pdf-engine-opt=--page-size", f"--pdf-engine-opt={page_size}",
    ]

    subprocess.run(pandoc_args, check=True, env=env)


    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    os.unlink(html_path)
    os.unlink(pdf_path)

    return Response(content=pdf_bytes, media_type="application/pdf")
