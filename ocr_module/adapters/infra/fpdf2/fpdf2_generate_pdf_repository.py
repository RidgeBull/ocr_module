import os
from io import BytesIO
from logging import getLogger
from typing import List, Tuple  # noqa: F401
from urllib.parse import quote
from urllib.request import urlopen

import numpy as np
from fpdf import FPDF
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from PIL import Image
from pypdf import PdfReader

from ocr_module.domain.entities import Section, Table, TextParagraph  # noqa: F401
from ocr_module.domain.repositories import IPDFGeneratorRepository  # noqa: F401


def convert_bbox_to_point(
    bbox: Tuple[float, float, float, float]
) -> Tuple[float, float, float, float]:
    """
    bboxは (xmin, ymin, xmax, ymax) の形式で、インチ(in)単位。
    fpdf2 での単位をポイント(pt)にするため、1インチ=72pt で換算。
    """
    return (
        bbox[0] * 72,
        bbox[1] * 72,
        bbox[2] * 72,
        bbox[3] * 72,
    )


class FPDF2GeneratePDFRepository(IPDFGeneratorRepository):
    def __init__(self):
        self.logger = getLogger(__name__)

    def generate_pdf(
        self, sections: List[Section], page_num: int, output_path: str
    ) -> str:
        # fpdf2 の初期化: 単位をptにし、マージンを0にする
        pdf = FPDF(unit="pt")  # 単位をポイントに
        pdf.set_auto_page_break(auto=False, margin=0)  # 自動改ページオフ & 余白0
        pdf.set_margins(left=0, top=0, right=0)  # 左上右マージン0
        pdf.set_font("Arial", size=12)

        self.logger.debug(f"Creating PDF with {page_num} pages (no margins).")

        for i in range(page_num):
            pdf.add_page()

        for section in sections:
            self._insert_section(pdf, section)

        self.logger.debug(f"PDF generation done. Saving to {output_path}")
        pdf.output(output_path, "F")
        return output_path

    def _insert_section(self, pdf: FPDF, section: Section):
        if section.paragraphs:
            self.logger.debug(
                f"Inserting {len(section.paragraphs)} paragraphs in section."
            )
            for paragraph in section.paragraphs:
                self._insert_paragraph(pdf, paragraph)

    def _insert_paragraph(self, pdf: FPDF, paragraph: TextParagraph):
        """
        paragraph.bboxは (xmin, ymin, xmax, ymax) (単位: インチ)
        fpdf2座標は左上が(0,0)で x→右, y→下。すべてポイント単位。
        """
        pdf.page = paragraph.page_number  # 1始まりのページ指定
        self.logger.debug(
            f"Moving to page {paragraph.page_number} for paragraph insertion."
        )

        # :formula: を数式に置換
        for formula in paragraph.inline_formulas:
            self.logger.debug(f"Replacing :formula: with ${formula}$")
            paragraph.text = paragraph.text.replace(":formula:", f"${formula}$", 1)
            self.logger.debug(f"Replaced text: {paragraph.text}")

        # bboxをポイントに変換
        bbox_pt = convert_bbox_to_point(paragraph.bbox)
        x_min, y_min, x_max, y_max = bbox_pt
        width_pt = x_max - x_min
        height_pt = y_max - y_min

        if paragraph.inline_formulas:
            # 数式を含む場合 → matplotlib で画像化して貼り付け
            self.logger.debug(f"Inserting paragraph with formula: {paragraph.text}")

            # 数式を画像化
            url = f"https://chart.googleapis.com/chart?cht=tx&chs=200&chl={quote(paragraph.text)}"

            with urlopen(url) as response:
                img = BytesIO(response.read())

            # fpdf2で画像貼付
            self.logger.debug(
                f"Placing formula image at x={x_min}, y={y_min}, w={width_pt}, h={height_pt}"
            )
            pdf.image(img, x_min, y_min, width_pt, height_pt)

            # 画像を保存（デバッグ用）
            debug_img_path = f"image_{paragraph.page_number}_{len(paragraph.lines)}.png"
            img.save(debug_img_path)
            self.logger.debug(f"Saved debug image: {debug_img_path}")

        else:
            # 通常のテキストだけ
            self.logger.debug(f"Inserting paragraph: {paragraph.text}")
            self.logger.debug(f"Placing text at x={x_min}, y={y_min}, width={width_pt}")
            pdf.set_xy(x_min, y_min)
            pdf.multi_cell(width_pt, 14, paragraph.text)  # 行間を14ptに
