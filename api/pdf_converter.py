from pydantic import BaseModel
from typing import Optional


class ConvertRequest(BaseModel):
    html: str
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


def _build_page_css(req: ConvertRequest) -> str:
    """Build a @page CSS block from the request margins and footer settings."""
    mt = f"{req.margin_top_mm}mm" if req.margin_top_mm is not None else "10mm"
    mb = f"{req.margin_bottom_mm}mm" if req.margin_bottom_mm is not None else "10mm"
    ml = f"{req.margin_left_mm}mm" if req.margin_left_mm is not None else "10mm"
    mr = f"{req.margin_right_mm}mm" if req.margin_right_mm is not None else "10mm"
    size = req.page_size or "A4"

    footer_fs = f"{req.footer_font_size}px" if isinstance(req.footer_font_size, int) else "8px"
    border_css = "border-top: 0.5px solid #ccc; padding-top: 4px;" if req.footer_line else ""

    margin_boxes = []

    if req.footer_left:
        margin_boxes.append(
            f"@bottom-left {{ content: '{_css_escape(req.footer_left)}';"
            f" font-size: {footer_fs}; color: #6a6e73; {border_css} }}"
        )
    if req.footer_center:
        margin_boxes.append(
            f"@bottom-center {{ content: '{_css_escape(req.footer_center)}';"
            f" font-size: {footer_fs}; color: #6a6e73; {border_css} }}"
        )
    if req.footer_right:
        footer_right_val = req.footer_right
        footer_right_val = footer_right_val.replace("[page]", "' counter(page) '")
        footer_right_val = footer_right_val.replace("[toPage]", "' counter(pages) '")
        margin_boxes.append(
            f"@bottom-right {{ content: '{footer_right_val}';"
            f" font-size: {footer_fs}; color: #6a6e73; {border_css} }}"
        )

    boxes_css = "\n".join(margin_boxes)
    return f"@page {{ size: {size}; margin: {mt} {mr} {mb} {ml};\n{boxes_css}\n}}"


def _css_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("'", "\\'")


def convert_to_pdf(req: ConvertRequest):
    page_css = _build_page_css(req)

    html_content = req.html
    inject_marker = "</style>"
    if inject_marker in html_content:
        html_content = html_content.replace(
            inject_marker,
            page_css + inject_marker,
            1,
        )
    else:
        html_content = f"<style>{page_css}</style>{html_content}"

    from weasyprint import HTML
    html_obj = HTML(string=html_content)
    pdf_bytes = html_obj.write_pdf()

    return pdf_bytes
