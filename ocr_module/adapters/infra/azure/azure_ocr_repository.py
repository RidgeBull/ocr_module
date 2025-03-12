import logging
import os
from logging import getLogger
from typing import Dict, List, Tuple

from azure.ai.documentintelligence.models import (
    AnalyzeResult,
    DocumentFigure,
    DocumentFormula,
    DocumentParagraph,
    DocumentPage,
    DocumentSection,
    DocumentTable,
)

from ocr_module.domain.entities import (
    DisplayFormula,
    Document,
    Figure,
    Formula,
    Page,
    Paragraph,
    Section,
    Table,
)
from ocr_module.domain.repositories import IImageExtractorRepository, IOCRRepository

from .azure_client import AzureDocumentIntelligenceClient


def _get_bounding_box(
    polygon: List[float], unit: str
) -> Tuple[float, float, float, float]:
    """polygonからbounding boxを取得する

    Args:
        polygon (List[float]): ポリゴンの座標
        unit (str): 単位（"pixel" or "inch"）
    Returns:
        tuple: bounding boxの座標
    """
    if unit == "pixel":
        x_coordinates = [polygon[i] / 96 for i in range(0, len(polygon), 2)]
        y_coordinates = [polygon[i] / 96 for i in range(1, len(polygon), 2)]
    elif unit == "inch":
        x_coordinates = [polygon[i] for i in range(0, len(polygon), 2)]
        y_coordinates = [polygon[i] for i in range(1, len(polygon), 2)]
    else:
        raise ValueError(f"Invalid unit: {unit}")
    return (
        min(x_coordinates),
        min(y_coordinates),
        max(x_coordinates),
        max(y_coordinates),
    )


def _convert_pixel_to_inch(
    pixel_width: float, pixel_height: float, unit: str
) -> Tuple[float, float]:
    """ピクセルをインチに変換する

    Args:
        pixel_width (float): ピクセル
        pixel_height (float): ピクセル
        unit (str): 単位
    """
    if unit == "pixel":
        return pixel_width / 96, pixel_height / 96
    elif unit == "inch":
        return pixel_width, pixel_height
    else:
        raise ValueError(f"Invalid unit: {unit}")


class AzureOCRRepository(IOCRRepository):
    def __init__(self, image_extractor: IImageExtractorRepository):
        self.client = AzureDocumentIntelligenceClient()
        self.image_extractor = image_extractor

        self.logger = getLogger(__name__)

    def get_document(self, document_path: str) -> Document:
        result = self.client.analyze_document_from_document_path(document_path)
        return Document(
            pages=self._analyze_result_to_pages(result, document_path),
            sections=self._analyze_result_to_sections(result, document_path),
        )

    def get_pages(self, document_path: str) -> List[Page]:
        result = self.client.analyze_document_from_document_path(document_path)
        return self._analyze_result_to_pages(result, document_path)

    def get_sections(self, document_path: str) -> List[Section]:
        result = self.client.analyze_document_from_document_path(document_path)
        return self._analyze_result_to_sections(result, document_path)

    def _analyze_result_to_pages(
        self, result: AnalyzeResult, document_path: str
    ) -> List[Page]:
        # ログディレクトリの設定
        log_dir = "logs/ocr"
        os.makedirs(log_dir, exist_ok=True)

        pages = result.pages
        paragraphs = result.paragraphs
        tables = result.tables
        figures = result.figures

        # ページごとにパラグラフ、テーブル、フィギュアを抽出
        if paragraphs is None:
            self.logger.warning("No paragraphs found")
            paragraphs_in_page = {i: [] for i in range(1, len(pages) + 1)}
        else:
            paragraphs_in_page = self.get_paragraphs_in_page(
                paragraphs, len(pages), pages
            )
        if tables is None:
            self.logger.warning("No tables found")
            tables_in_page = {i: [] for i in range(1, len(pages) + 1)}
        else:
            tables_in_page = self.get_tables_in_page(
                tables, document_path, len(pages), pages
            )
        if figures is None:
            self.logger.warning("No figures found")
            figures_in_page = {i: [] for i in range(1, len(pages) + 1)}
        else:
            figures_in_page = self.get_figures_in_page(
                figures, document_path, len(pages), pages
            )

        # display_formulaとformulaのdict
        display_formulas_in_page: Dict[int, List[DisplayFormula]] = {
            i: [] for i in range(1, len(pages) + 1)
        }
        formulas_in_page: Dict[int, List[Formula]] = {
            i: [] for i in range(1, len(pages) + 1)
        }
        for page_number, page in enumerate(pages, 1):
            if page.formulas is None:
                self.logger.warning(f"Page {page_number} has no formulas")
                formulas_in_page[page_number] = []
                display_formulas_in_page[page_number] = []
                continue
            else:
                formulas_in_page[page_number] = [
                    Formula(
                        formula_id=idx,
                        latex_value=formula.value,
                        bbox=_get_bounding_box(
                            formula.polygon or [0, 0, 0, 0],
                            pages[page_number - 1].unit or "pixel",
                        ),
                        type="inline" if formula.kind == "inline" else "display",
                        page_number=page_number,
                    )
                    for idx, formula in enumerate(page.formulas)
                ]
                display_formulas_in_page[page_number] = (
                    self.get_display_formulas_in_page(
                        page_number, page.formulas, document_path, pages
                    )
                )

        pages_entity: List[Page] = []
        for page_number, page in enumerate(pages, 1):
            # ページごとのログファイルを設定
            page_logger = getLogger(f"page_{page_number}")
            page_logger.setLevel(logging.INFO)
            for handler in page_logger.handlers:
                page_logger.removeHandler(handler)

            log_path = os.path.join(log_dir, f"page_{page_number}.log")
            handler = logging.FileHandler(log_path, mode="w")
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            page_logger.addHandler(handler)

            # ページの基本情報を記録
            page_logger.debug(f"=== Page {page_number} Analysis ===")
            page_logger.debug(
                f"Page size: {page.width or 0.0}[{page.unit}]x{page.height or 0.0}[{page.unit}] inches\n"
            )
            if page.formulas is not None:
                for formula in page.formulas:
                    page_logger.debug(f"Formula: {formula.value}")

            # パラグラフ内の:formula:トークンを分析
            page_paragraphs = paragraphs_in_page[page_number]
            total_formula_tokens = sum(
                p.content.count(":formula:") for p in page_paragraphs
            )

            # 実際の数式の数を取得
            page_formulas = formulas_in_page[page_number]

            page_logger.debug(f"Number of paragraphs: {len(page_paragraphs)}")
            page_logger.debug(
                f"Total :formula: tokens in paragraphs: {total_formula_tokens}"
            )
            page_logger.debug(f"Actual formulas available: {len(page_formulas)}")

            # 不一致がある場合は警告
            if total_formula_tokens != len(page_formulas):
                page_logger.warning(
                    f"Mismatch between :formula: tokens ({total_formula_tokens}) "
                    f"and available formulas ({len(page_formulas)})"
                )

            # 各パラグラフの詳細情報を記録
            for i, paragraph in enumerate(page_paragraphs):
                formula_count = paragraph.content.count(":formula:")
                page_logger.debug(
                    f"Paragraph {i}: {formula_count} :formula: tokens\n"
                    f"Content: {paragraph.content}"
                )

            # ページサイズをインチに変換
            page_size = _convert_pixel_to_inch(
                page.width or 0.0, page.height or 0.0, page.unit or "pixel"
            )
            # ページエンティティの作成
            page_entity = Page(
                width=page_size[0],
                height=page_size[1],
                formulas=formulas_in_page[page_number],
                page_number=page_number,
                paragraphs=paragraphs_in_page[page_number],
                tables=tables_in_page[page_number],
                figures=figures_in_page[page_number],
                display_formulas=display_formulas_in_page[page_number],
            )
            pages_entity.append(page_entity)

        return pages_entity

    def _analyze_result_to_sections(
        self, result: AnalyzeResult, document_path: str
    ) -> List[Section]:
        sections = result.sections
        paragraphs = result.paragraphs
        tables = result.tables
        figures = result.figures
        pages = result.pages

        if sections is None:
            self.logger.warning("No sections or paragraphs found")
            return []

        sections_list: List[Section] = []
        for idx, section in enumerate(sections):
            if paragraphs is None:
                self.logger.warning("No paragraphs found")
                section_paragraphs = []
                section_paragraph_ids = []
            else:
                section_paragraphs, section_paragraph_ids = (
                    self.get_paragraphs_in_section(paragraphs, section, pages)
                )
            if tables is None:
                self.logger.warning("No tables found")
                section_tables = []
                section_table_ids = []
            else:
                section_tables, section_table_ids = self.get_tables_in_section(
                    tables, document_path, section, pages
                )
            if figures is None:
                self.logger.warning("No figures found")
                section_figures = []
                section_figure_ids = []
            else:
                section_figures, section_figure_ids = self.get_figures_in_section(
                    figures, document_path, section, pages
                )
            section_entity = Section(
                section_id=idx,
                paragraphs=section_paragraphs,
                tables=section_tables,
                figures=section_figures,
                paragraph_ids=section_paragraph_ids,
                table_ids=section_table_ids,
                figure_ids=section_figure_ids,
            )
            sections_list.append(section_entity)
        return sections_list

    def get_paragraphs_in_page(
        self,
        paragraphs: List[DocumentParagraph],
        num_pages: int,
        pages: List[DocumentPage],
    ) -> Dict[int, List[Paragraph]]:
        """ページごとにパラグラフを抽出する

        Args:
            paragraphs (List[DocumentParagraph]): パラグラフのリスト
            num_pages (int): ページ数
            pages (List[DocumentPage]): ページのリスト

        Returns:
            Dict[int, List[Paragraph]]: ページごとのパラグラフのリスト
        """
        pararaphs_in_page: Dict[int, List[Paragraph]] = {
            i: [] for i in range(1, num_pages + 1)
        }
        for idx, paragraph in enumerate(paragraphs):
            if paragraph.bounding_regions is None:
                continue
            page_number = paragraph.bounding_regions[0].page_number
            paragraph_entity = Paragraph(
                paragraph_id=idx,
                role=paragraph.role,
                content=paragraph.content,
                bbox=_get_bounding_box(
                    paragraph.bounding_regions[0].polygon,
                    pages[page_number - 1].unit or "pixel",
                ),
                page_number=page_number,
            )
            pararaphs_in_page[page_number].append(paragraph_entity)
        return pararaphs_in_page

    def get_figures_in_page(
        self,
        figures: List[DocumentFigure],
        document_path: str,
        num_pages: int,
        pages: List[DocumentPage],
    ) -> Dict[int, List[Figure]]:
        """ページごとにフィギュアを抽出する

        Args:
            figures (List[DocumentFigure]): フィギュアのリスト
            document_path (str): ドキュメントのパス
            num_pages (int): ページ数
            pages (List[DocumentPage]): ページのリスト

        Returns:
            Dict[int, List[Figure]]: ページごとのフィギュアのリスト
        """
        figures_in_page: Dict[int, List[Figure]] = {
            i: [] for i in range(1, num_pages + 1)
        }
        for idx, figure in enumerate(figures):
            if figure.bounding_regions is None:
                continue
            page_number = figure.bounding_regions[0].page_number
            image_data = self.image_extractor.extract_image(
                pdf_path=document_path,
                page_number=page_number,
                inch_bbox=_get_bounding_box(
                    figure.bounding_regions[0].polygon,
                    pages[page_number - 1].unit or "pixel",
                ),
            )
            figure_element_ids: List[int] = []
            if figure.elements is not None:
                figure_element_ids = [
                    int(element.split("/")[-1]) for element in figure.elements
                ]
            figure_entity = Figure(
                figure_id=idx,
                bbox=_get_bounding_box(
                    figure.bounding_regions[0].polygon,
                    pages[page_number - 1].unit or "pixel",
                ),
                page_number=page_number,
                image_data=image_data,
                element_paragraph_ids=figure_element_ids,
            )
            figures_in_page[page_number].append(figure_entity)
        return figures_in_page

    def get_tables_in_page(
        self,
        tables: List[DocumentTable],
        document_path: str,
        num_pages: int,
        pages: List[DocumentPage],
    ) -> Dict[int, List[Table]]:
        """ページごとにテーブルを抽出する

        Args:
            tables (List[DocumentTable]): テーブルのリスト
            document_path (str): ドキュメントのパス
            num_pages (int): ページ数
            pages (List[DocumentPage]): ページのリスト

        Returns:
            Dict[int, List[Table]]: ページごとのテーブルのリスト
        """
        tables_in_page: Dict[int, List[Table]] = {
            i: [] for i in range(1, num_pages + 1)
        }
        for idx, table in enumerate(tables):
            if table.bounding_regions is None:
                continue
            page_number = table.bounding_regions[0].page_number
            image_data = self.image_extractor.extract_image(
                pdf_path=document_path,
                page_number=page_number,
                inch_bbox=_get_bounding_box(
                    table.bounding_regions[0].polygon,
                    pages[page_number - 1].unit or "pixel",
                ),
            )
            table_element_ids: List[int] = []
            if table.cells is not None:
                for cell in table.cells:
                    if cell.elements is not None:
                        table_element_ids.extend(
                            [int(element.split("/")[-1]) for element in cell.elements]
                        )

            table_entity = Table(
                table_id=idx,
                bbox=_get_bounding_box(
                    table.bounding_regions[0].polygon,
                    pages[page_number - 1].unit or "pixel",
                ),
                page_number=page_number,
                image_data=image_data,
                element_paragraph_ids=table_element_ids,
            )
            tables_in_page[page_number].append(table_entity)
        return tables_in_page

    def get_display_formulas_in_page(
        self,
        page_number: int,
        formulas: List[DocumentFormula],
        document_path: str,
        pages: List[DocumentPage],
    ) -> List[DisplayFormula]:
        """ページごとに表示数式を抽出する

        Args:
            page_number (int): ページ番号
            formulas (List[DocumentFormula]): 数式のリスト
            document_path (str): ドキュメントのパス
            pages (List[DocumentPage]): ページのリスト

        Returns:
            List[DisplayFormula]: ページごとの表示数式のリスト
        """
        display_formulas: List[DisplayFormula] = []
        formulas = [formula for formula in formulas if formula.kind == "display"]
        for idx, formula in enumerate(formulas):
            if formula.polygon is None:
                continue
            image_data = self.image_extractor.extract_image(
                pdf_path=document_path,
                page_number=page_number,
                inch_bbox=_get_bounding_box(
                    formula.polygon, pages[page_number - 1].unit or "pixel"
                ),
            )
            display_forumla_entity = DisplayFormula(
                formula_id=idx,
                latex_value=formula.value,
                bbox=_get_bounding_box(
                    formula.polygon, pages[page_number - 1].unit or "pixel"
                ),
                type="display",
                page_number=page_number,
                image_data=image_data,
            )
            display_formulas.append(display_forumla_entity)
        return display_formulas

    def get_paragraphs_in_section(
        self,
        paragraphs: List[DocumentParagraph],
        section: DocumentSection,
        pages: List[DocumentPage],
    ) -> Tuple[List[Paragraph], List[int]]:
        """セクションごとにパラグラフを抽出する

        Args:
            paragraphs (List[DocumentParagraph]): パラグラフのリスト
            section (DocumentSection): セクション
            pages (List[DocumentPage]): ページのリスト

        Returns:
            Tuple[List[Paragraph], List[int]]: セクションごとのパラグラフのリストとパラグラフのIDのリスト
        """
        elements = section.elements
        if elements is None:
            return [], []
        paragraphs_ids = [
            element.split("/")[-1]
            for element in elements
            if element.startswith("/paragraphs/")
        ]
        paragraphs_in_section: List[Paragraph] = []
        for paragraph_id in paragraphs_ids:
            paragraph = paragraphs[int(paragraph_id)]
            if paragraph.bounding_regions is None:
                continue
            page_number = paragraph.bounding_regions[0].page_number
            paragraph_entity = Paragraph(
                paragraph_id=int(paragraph_id),
                role=paragraph.role,
                content=paragraph.content,
                bbox=_get_bounding_box(
                    paragraph.bounding_regions[0].polygon,
                    pages[page_number - 1].unit or "pixel",
                ),
                page_number=page_number,
            )
            paragraphs_in_section.append(paragraph_entity)
        return paragraphs_in_section, [
            int(paragraph_id) for paragraph_id in paragraphs_ids
        ]

    def get_tables_in_section(
        self,
        tables: List[DocumentTable],
        document_path: str,
        section: DocumentSection,
        pages: List[DocumentPage],
    ) -> Tuple[List[Table], List[int]]:
        """セクションごとにテーブルを抽出する

        Args:
            tables (List[DocumentTable]): テーブルのリスト
            document_path (str): ドキュメントのパス
            section (DocumentSection): セクション
            pages (List[DocumentPage]): ページのリスト

        Returns:
            Tuple[List[Table], List[int]]: セクションごとのテーブルのリストとテーブルのIDのリスト
        """
        elements = section.elements
        tables_ids = [
            element.split("/")[-1]
            for element in elements
            if element.startswith("/tables/")
        ]
        tables_in_section: List[Table] = []
        for table_id in tables_ids:
            table = tables[int(table_id)]
            if table.bounding_regions is None:
                continue
            image_data = self.image_extractor.extract_image(
                pdf_path=document_path,
                page_number=table.bounding_regions[0].page_number,
                inch_bbox=_get_bounding_box(
                    table.bounding_regions[0].polygon,
                    pages[table.bounding_regions[0].page_number - 1].unit or "pixel",
                ),
            )
            table_element_ids: List[int] = []
            if table.cells is not None:
                for cell in table.cells:
                    if cell.elements is not None:
                        table_element_ids.extend(
                            [int(element.split("/")[-1]) for element in cell.elements]
                        )
            table_entity = Table(
                table_id=int(table_id),
                bbox=_get_bounding_box(
                    table.bounding_regions[0].polygon,
                    pages[table.bounding_regions[0].page_number - 1].unit or "pixel",
                ),
                page_number=table.bounding_regions[0].page_number,
                image_data=image_data,
                element_paragraph_ids=table_element_ids,
            )
            tables_in_section.append(table_entity)
        return tables_in_section, [int(table_id) for table_id in tables_ids]

    def get_figures_in_section(
        self,
        figures: List[DocumentFigure],
        document_path: str,
        section: DocumentSection,
        pages: List[DocumentPage],
    ) -> Tuple[List[Figure], List[int]]:
        """セクションごとにフィギュアを抽出する

        Args:
            figures (List[DocumentFigure]): フィギュアのリスト
            document_path (str): ドキュメントのパス
            section (DocumentSection): セクション
            pages (List[DocumentPage]): ページのリスト

        Returns:
            Tuple[List[Figure], List[int]]: セクションごとのフィギュアのリストとフィギュアのIDのリスト
        """
        elements = section.elements
        figures_ids = [
            element.split("/")[-1]
            for element in elements
            if element.startswith("/figures/")
        ]
        figures_in_section: List[Figure] = []
        for figure_id in figures_ids:
            figure = figures[int(figure_id)]
            if figure.bounding_regions is None:
                continue
            image_data = self.image_extractor.extract_image(
                pdf_path=document_path,
                page_number=figure.bounding_regions[0].page_number,
                inch_bbox=_get_bounding_box(
                    figure.bounding_regions[0].polygon,
                    pages[figure.bounding_regions[0].page_number - 1].unit or "pixel",
                ),
            )
            figure_element_ids: List[int] = []
            if figure.elements is not None:
                figure_element_ids = [
                    int(element.split("/")[-1]) for element in figure.elements
                ]
            figure_entity = Figure(
                figure_id=int(figure_id),
                bbox=_get_bounding_box(
                    figure.bounding_regions[0].polygon,
                    pages[figure.bounding_regions[0].page_number - 1].unit or "pixel",
                ),
                page_number=figure.bounding_regions[0].page_number,
                image_data=image_data,
                element_paragraph_ids=figure_element_ids,
            )
            figures_in_section.append(figure_entity)
        return figures_in_section, [int(figure_id) for figure_id in figures_ids]
