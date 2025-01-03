import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import List, Literal, Tuple

from azure.ai.documentintelligence.models import (
    DocumentFigure,
    DocumentFormula,
    DocumentPage,
    DocumentParagraph,
    DocumentSection,
    DocumentSpan,
    DocumentStyle,
    DocumentTable,
)
from ocr_module.domain.entities import (
    Caption,
    Cell,
    DisplayFormula,
    Figure,
    Section,
    Table,
    TextLine,
    TextParagraph,
)
from ocr_module.domain.repositories import IImageExtractorRepository, IOcrRepository
from utils.logger import setup_function_logger

from .azure_client import AzureDocumentIntelligenceClient


@dataclass
class _TextLine:
    text: str
    inline_formulas: List[DocumentFormula]
    bbox: tuple  # (xmin, ymin, xmax, ymax)
    font: str
    color_hex: str
    font_weight: Literal["bold", "normal"]
    background_color_hex: str
    span: DocumentSpan


@dataclass
class _TextParagraph:
    text: str
    inline_formulas: List[DocumentFormula]
    lines: List[TextLine]
    bbox: tuple
    page_number: int


def _get_line_style(line_span: DocumentSpan, styles: List[DocumentStyle]) -> dict:
    style_attributes = {
        "font": None,
        "color": None,
        "font_weight": None,
        "background_color": None,
    }

    def binary_search_span(spans: List[DocumentSpan], target_offset: int) -> int:
        left, right = 0, len(spans) - 1
        while left <= right:
            mid = (left + right) // 2
            span = spans[mid]
            if span.offset <= target_offset < span.offset + span.length:
                return mid
            elif target_offset < span.offset:
                right = mid - 1
            else:
                left = mid + 1
        return -1

    for style in styles:
        spans = style.spans
        idx = binary_search_span(spans, line_span.offset)
        if idx != -1:
            if style.similar_font_family:
                style_attributes["font"] = style.similar_font_family
            if style.color:
                style_attributes["color"] = style.color
            if style.font_weight:
                style_attributes["font_weight"] = style.font_weight
            if style.background_color:
                style_attributes["background_color"] = style.background_color

    return style_attributes


def _get_bounding_box(polygon: List[float]) -> tuple:
    x_coordinates = [polygon[i] for i in range(0, len(polygon), 2)]
    y_coordinates = [polygon[i] for i in range(1, len(polygon), 2)]
    return (
        min(x_coordinates),
        min(y_coordinates),
        max(x_coordinates),
        max(y_coordinates),
    )


def _get_textlines_in_paragraph(
    paragraph: DocumentParagraph, text_lines: List[_TextLine]
) -> List[_TextLine]:
    paragraph_span = paragraph.spans[0]
    start_offset = paragraph_span.offset
    end_offset = start_offset + paragraph_span.length

    # 開始位置を二分探索
    def binary_search_start(lines: List[_TextLine], target: int) -> int:
        left, right = 0, len(lines) - 1
        result = len(lines)
        while left <= right:
            mid = (left + right) // 2
            if lines[mid].span.offset >= target:
                result = mid
                right = mid - 1
            else:
                left = mid + 1
        return result

    # 終了位置を二分探索
    def binary_search_end(lines: List[_TextLine], target: int) -> int:
        left, right = 0, len(lines) - 1
        result = -1
        while left <= right:
            mid = (left + right) // 2
            if lines[mid].span.offset < target:
                result = mid
                left = mid + 1
            else:
                right = mid - 1
        return result

    start_idx = binary_search_start(text_lines, start_offset)
    end_idx = binary_search_end(text_lines, end_offset)
    return text_lines[start_idx : end_idx + 1]


class AzureOcrRepository(IOcrRepository):
    def __init__(self, image_extractor: IImageExtractorRepository):
        self.client = AzureDocumentIntelligenceClient()
        self.logger = getLogger(__name__)
        self.image_extractor = image_extractor

        # 各関数用のパフォーマンスロガーを設定
        self.analyze_section_logger = setup_function_logger("analyze_section")
        self.analyze_page_logger = setup_function_logger("analyze_page")
        self.analyze_paragraph_logger = setup_function_logger("analyze_paragraph")
        self.get_line_style_logger = setup_function_logger("get_line_style")
        self.get_textlines_logger = setup_function_logger("get_textlines")

        # ページ解析結果をキャッシュするための辞書
        # { page_number: {"text_lines": [...], "display_formulas": [...]} }
        self._page_cache = {}

    def get_sections(self, document_path: str) -> List[Section]:
        print(f"Reading document from path: {document_path}")
        self.document_path = document_path
        self._read_document(document_path)
        sections = self._get_sections()
        return sections

    def get_display_formulas(self) -> List[DisplayFormula]:
        display_formulas: List[DisplayFormula] = []
        for page in self.pages:
            if not page.formulas:
                continue
            for formula in page.formulas:
                if formula.kind == "display":
                    display_formulas.append(
                        DisplayFormula(
                            latex_value=formula.value,
                            bbox=_get_bounding_box(formula.polygon),
                            page_number=page.page_number,
                            image_data=self.image_extractor.extract_image(
                                self.document_path,
                                page.page_number,
                                _get_bounding_box(formula.polygon),
                            ),
                        )
                    )
        return display_formulas

    def get_page_number(self) -> int:
        return len(self.pages)

    def get_page_size(self) -> Tuple[float, float]:
        pages = self.pages
        # number of lines in each page
        for page in pages:
            print(f"Page {page.page_number}: {len(page.lines)} lines")
        if not pages:
            return (0, 0)
        return (pages[0].width, pages[0].height)

    def _read_document(self, document_path: str):
        self.result = self.client.analyze_document_from_document_path(document_path)

        # OCR結果保存用のディレクトリを作成
        ocr_result_dir = Path("logs/ocr_results")
        ocr_result_dir.mkdir(parents=True, exist_ok=True)

        # ファイル名から識別子を生成
        file_id = Path(document_path).stem

        if self.result.pages:
            self.pages = self.result.pages
            # ページごとのOCR結果を保存
            for page in self.pages:
                result_file = ocr_result_dir / f"{file_id}_page_{page.page_number}.txt"
                self._save_page_result(page, result_file)

        if self.result.sections:
            self.sections = self.result.sections
        if self.result.paragraphs:
            self.paragraphs = self.result.paragraphs
        if self.result.figures:
            self.figures = self.result.figures
        if self.result.tables:
            self.tables = self.result.tables
        if self.result.styles:
            self.styles = self.result.styles

        # --- ここで各ページをまめて解析してキャッシュに格納 ---
        self._preprocess_pages()

    def _save_page_result(self, page: DocumentPage, output_file: Path):
        """ページごとのOCR結果を保存"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"=== Page {page.page_number} ===\n")
            f.write(f"Size: {page.width}x{page.height}\n")
            f.write(f"Number of lines: {len(page.lines)}\n\n")

            # テキスト行の保存
            f.write("--- Text Lines ---\n")
            for line in page.lines:
                f.write(f"Content: {line.content}\n")
                f.write(f"Bbox: {_get_bounding_box(line.polygon)}\n")
                f.write("\n")

            # 数式の保存
            if page.formulas:
                f.write("\n--- Formulas ---\n")
                for formula in page.formulas:
                    f.write(f"Type: {formula.kind}\n")
                    f.write(f"Value: {formula.value}\n")
                    if formula.polygon:
                        f.write(f"Bbox: {_get_bounding_box(formula.polygon)}\n")
                    f.write("\n")

    def _preprocess_pages(self):
        with ThreadPoolExecutor() as executor:
            future_to_page = {
                executor.submit(self._analyze_page, page): page for page in self.pages
            }
            for future in as_completed(future_to_page):
                original_page = future_to_page[future]  # 元のページオブジェクトを取得
                try:
                    text_lines, display_formulas, inline_formulas = future.result()
                    self._page_cache[original_page.page_number] = {
                        "text_lines": text_lines,
                        "display_formulas": display_formulas,
                        "inline_formulas": inline_formulas,
                    }
                except Exception as e:
                    self.logger.error(f"Failed to analyze page: {e}", exc_info=True)

    def _analyze_page(
        self, document_page: DocumentPage
    ) -> Tuple[List[_TextLine], List[DocumentFormula], List[DocumentFormula]]:
        start_time = time.time()
        try:
            # ページ内のformulaを取得
            formulas: List[DocumentFormula] = (
                document_page.formulas if document_page.formulas else []
            )

            # inline formulaを取得
            inline_formulas: List[DocumentFormula] = [
                formula for formula in formulas if formula.kind == "inline"
            ]

            # display formulaを取得（返り値にも含める）
            display_formulas: List[DocumentFormula] = [
                formula for formula in formulas if formula.kind == "display"
            ]

            # ページ内の lines を取得
            lines = document_page.lines or []

            # text_lines を格納
            text_lines: List[_TextLine] = []
            current_inline_formula_idx = 0

            for line in lines:
                start_line_style_time = time.time()
                style = _get_line_style(line.spans[0], self.styles)
                elapsed_line_style_time = time.time() - start_line_style_time
                self.get_line_style_logger.info(f"{elapsed_line_style_time:.6f}")
                # line.content 内にある ':formula:' の数をカウントし、
                # 対応する個数だけ inline_formulas を割り当てる想定
                num_formula = line.content.count(":formula:")
                line_formulas = inline_formulas[
                    current_inline_formula_idx : current_inline_formula_idx
                    + num_formula
                ]
                current_inline_formula_idx += num_formula

                text_lines.append(
                    _TextLine(
                        text=line.content,
                        inline_formulas=line_formulas,
                        bbox=_get_bounding_box(line.polygon),
                        font=style["font"],
                        color_hex=style["color"],
                        font_weight=style["font_weight"],
                        background_color_hex=style["background_color"],
                        span=line.spans[0],
                    )
                )
                self.logger.debug(f"Line: {line.content} with style: {style}")

            return text_lines, display_formulas, inline_formulas
        finally:
            elapsed_time = time.time() - start_time
            self.analyze_page_logger.info(f"{elapsed_time:.6f}")

    def _analyze_page_paragraphs(
        self,
        page: DocumentPage,
        paragraphs: List[DocumentParagraph],
        text_lines: List[_TextLine],
    ) -> List[_TextParagraph]:
        inline_formulas = [
            formula for formula in page.formulas if formula.kind == "inline"
        ]
        current_inline_formula_idx = 0
        text_paragraphs: List[_TextParagraph] = []
        for paragraph in paragraphs:
            num_formula = paragraph.content.count(":formula:")
            line_formulas = inline_formulas[
                current_inline_formula_idx : current_inline_formula_idx + num_formula
            ]
            current_inline_formula_idx += num_formula
            text_lines = _get_textlines_in_paragraph(paragraph, text_lines)
            text_paragraphs.append(
                _TextParagraph(
                    text=paragraph.content,
                    inline_formulas=line_formulas,
                    lines=[
                        TextLine(
                            text=line.text,
                            inline_formulas=[f.value for f in line.inline_formulas],
                            bbox=line.bbox,
                            font=line.font,
                            color_hex=line.color_hex,
                            font_weight=line.font_weight,
                            background_color_hex=line.background_color_hex,
                        )
                        for line in text_lines
                    ],
                    bbox=_get_bounding_box(paragraph.bounding_regions[0].polygon),
                    page_number=paragraph.bounding_regions[0].page_number,
                )
            )
        return text_paragraphs

    def _analyze_paragraph(
        self,
        paragraph: DocumentParagraph,
        text_lines: List[_TextLine],
        inline_formulas: List[DocumentFormula],
    ) -> _TextParagraph:
        start_time = time.time()
        if not paragraph.bounding_regions:
            return _TextParagraph(
                text="",
                inline_formulas=[],
                lines=[],
                bbox=(0, 0, 0, 0),
                page_number=0,
            )
        start_textlines_time = time.time()
        self.get_textlines_logger.info(
            f"get_textlines_in_paragraph {paragraph.content}"
        )
        paragraph_text_lines = _get_textlines_in_paragraph(paragraph, text_lines)
        elapsed_textlines_time = time.time() - start_textlines_time
        self.get_textlines_logger.info(f"{elapsed_textlines_time:.6f}")
        paragraph_text = "".join([line.text for line in paragraph_text_lines])
        text_paragraph = _TextParagraph(
            text=paragraph_text,
            inline_formulas=[
                formula
                for text_line in paragraph_text_lines
                for formula in text_line.inline_formulas
            ],
            lines=[
                TextLine(
                    text=line.text,
                    inline_formulas=[f.value for f in line.inline_formulas],
                    bbox=line.bbox,
                    font=line.font,
                    color_hex=line.color_hex,
                    font_weight=line.font_weight,
                    background_color_hex=line.background_color_hex,
                )
                for line in paragraph_text_lines
            ],
            bbox=_get_bounding_box(paragraph.bounding_regions[0].polygon),
            page_number=paragraph.bounding_regions[0].page_number,
        )
        elapsed_time = time.time() - start_time
        self.analyze_paragraph_logger.info(f"{elapsed_time:.6f}")
        return text_paragraph

    def _analyze_figure(self, figure: DocumentFigure) -> Figure:
        if not figure.bounding_regions:
            return Figure(
                bbox=(0, 0, 0, 0),
                page_number=0,
                caption=Caption(bbox=(0, 0, 0, 0), content=""),
            )
        bbox = _get_bounding_box(figure.bounding_regions[0].polygon)
        page_number = figure.bounding_regions[0].page_number
        if not figure.caption:
            return Figure(
                bbox=bbox,
                page_number=page_number,
                caption=Caption(bbox=(0, 0, 0, 0), content=""),
            )
        caption = Caption(
            bbox=_get_bounding_box(figure.caption.bounding_regions[0].polygon),
            content=figure.caption.content,
        )
        figure_with_image = Figure(
            bbox=bbox,
            page_number=page_number,
            caption=caption,
            image_data=self.image_extractor.extract_image(
                self.document_path,
                page_number,
                bbox,
            ),
        )
        return figure_with_image

    def _analyze_table(self, table: DocumentTable) -> Table:
        if not table.bounding_regions:
            return Table(
                row_num=0,
                col_num=0,
                cells=[],
                bbox=(0, 0, 0, 0),
                page_number=0,
                caption=Caption(bbox=(0, 0, 0, 0), content=""),
            )
        bbox = _get_bounding_box(table.bounding_regions[0].polygon)
        page_number = table.bounding_regions[0].page_number
        cells = []
        for cell in table.cells:
            if not cell.bounding_regions:
                continue
            cell_bbox = _get_bounding_box(cell.bounding_regions[0].polygon)
            cells.append(
                Cell(
                    row_index=cell.row_index,
                    column_index=cell.column_index,
                    content=cell.content,
                    bbox=cell_bbox,
                )
            )
        image_data = self.image_extractor.extract_image(
            self.document_path,
            page_number,
            bbox,
        )
        print(f"Extracting image data for table: {bbox}")

        caption = Caption(bbox=(0, 0, 0, 0), content="")
        if table.caption and table.caption.bounding_regions:
            caption = Caption(
                bbox=_get_bounding_box(table.caption.bounding_regions[0].polygon),
                content=table.caption.content,
            )

        return Table(
            row_num=table.row_count,
            col_num=table.column_count,
            cells=cells,
            bbox=bbox,
            page_number=page_number,
            caption=caption,
            image_data=image_data,
        )

    def _analyze_section(self, section: DocumentSection) -> Section:
        start_time = time.time()
        try:
            if not section.elements:
                return Section(paragraphs=[], formula_blocks=[], tables=[], figures=[])

            elements = section.elements
            paragraph_ids = [
                element.split("/")[-1]
                for element in elements
                if element.startswith("/paragraphs/")
            ]
            figure_ids = [
                element.split("/")[-1]
                for element in elements
                if element.startswith("/figures/")
            ]
            table_ids = [
                element.split("/")[-1]
                for element in elements
                if element.startswith("/tables/")
            ]

            paragraphs: List[TextParagraph] = []
            for paragraph_id in paragraph_ids:
                paragraph = self.paragraphs[int(paragraph_id)]
                if not paragraph.bounding_regions:
                    continue

                # --- 以前はこで _analyze_page(page) を呼んでいたが、今はキャッシュを利用 ---
                page_number = paragraph.bounding_regions[0].page_number
                text_lines = self._page_cache[page_number]["text_lines"]
                # 必要に応じて display_formulas なども参照可能
                # display_formulas = self._page_cache[page_number]["display_formulas"]
                inline_formulas = self._page_cache[page_number]["inline_formulas"]
                analyzed_paragraph = self._analyze_paragraph(
                    paragraph, text_lines, inline_formulas
                )
                paragraphs.append(
                    TextParagraph(
                        text=analyzed_paragraph.text,
                        inline_formulas=[
                            formula.value
                            for formula in analyzed_paragraph.inline_formulas
                        ],
                        lines=[
                            TextLine(
                                text=line.text,
                                inline_formulas=line.inline_formulas,
                                bbox=line.bbox,
                                font=line.font,
                                color_hex=line.color_hex,
                                font_weight=line.font_weight,
                                background_color_hex=line.background_color_hex,
                            )
                            for line in analyzed_paragraph.lines
                        ],
                        bbox=analyzed_paragraph.bbox,
                        page_number=analyzed_paragraph.page_number,
                    )
                )

            figures: List[Figure] = []
            for figure_id in figure_ids:
                figure = self.figures[int(figure_id)]
                figure = self._analyze_figure(figure)
                figures.append(figure)

            tables: List[Table] = []
            for table_id in table_ids:
                table = self.tables[int(table_id)]
                table = self._analyze_table(table)
                tables.append(table)

            return Section(
                paragraphs=paragraphs,
                formula_blocks=[],  # 今回は空のまま
                tables=tables,
                figures=figures,
            )
        finally:
            elapsed_time = time.time() - start_time
            self.analyze_section_logger.info(f"{elapsed_time:.6f}")

    def _get_sections(self) -> List[Section]:
        sections: List[Section] = []
        with ThreadPoolExecutor() as executor:
            future_to_section = {
                executor.submit(self._analyze_section, section): section
                for section in self.sections
            }
            for future in as_completed(future_to_section):
                try:
                    analyzed_section = future.result()
                    sections.append(analyzed_section)
                except Exception as e:
                    self.logger.error(f"Failed to analyze section: {e}", exc_info=True)
        return sections
