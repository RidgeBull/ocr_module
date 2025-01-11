import logging
import os
import re
from logging import getLogger
from typing import Dict, List, Tuple

from pylatex import (
    Command,
    Document,
    Foot,
    FootnoteText,
    Head,
    MiniPage,
    Section,
    TextBlock,
)
from pylatex.package import Package
from pylatex.utils import NoEscape, escape_latex

from ocr_module.domain.entities import (
    DisplayFormula,
    Figure,
    Formula,
    Page,
    PageWithTranslation,
    Paragraph,
    ParagraphWithTranslation,
    Table,
)
from ocr_module.domain.repositories import IPDFGeneratorRepository


class PyLaTeXGeneratePDFRepository(IPDFGeneratorRepository):
    def __init__(self):
        self.logger = getLogger(__name__)
        # paragraphを処理する際のロガー
        self.paragraph_logger = getLogger("paragraph")
        # すでに設定されているハンドラを削除して、新しいハンドラを設定してファイルに出力する
        # for handler in self.paragraph_logger.handlers:
        #     self.paragraph_logger.removeHandler(handler)
        # # modeを'w'に設定して上書きモードにする
        # handler = logging.FileHandler("paragraph.log", mode="w")
        # handler.setFormatter(
        #     logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        # )
        # self.paragraph_logger.addHandler(handler)
        # ログレベルをDEBUGに設定
        self.paragraph_logger.setLevel(logging.INFO)

    def generate_pdf(self, page: Page, output_path: str):
        self.output_dir = os.path.dirname(output_path)
        geometry_options = {
            "margin": "0.0in",
            "paperwidth": f"{page.width}in",
            "paperheight": f"{page.height}in",
            "top": "0in",
            "bottom": "0in",
            "left": "0in",
            "right": "0in",
        }
        document = Document(geometry_options=geometry_options)
        document.packages.append(Package("textpos", options=["absolute"]))
        document.packages.append(Package("amsmath"))
        document.packages.append(Package("amssymb"))
        document.packages.append(Package("amsfonts"))
        document.packages.append(Package("graphicx"))
        document.packages.append(Package("tcolorbox", options=["fitting"]))
        document.packages.append(Package("CJK"))

        # 単位をインチに設定
        document.change_length(r"\TPHorizModule", "1in")
        document.change_length(r"\TPVertModule", "1in")

        # tcolorboxの設定
        document.append(
            NoEscape(
                r"""
            \tcbset{
                frame empty,  % 枠線なし
                interior empty,  % 背景なし
                boxsep=0pt,
                top=0pt,bottom=0pt,
                left=0pt,right=0pt,
                nobeforeafter,
                arc=0pt,
                outer arc=0pt,
                valign=center
            }
            """
            )
        )

        # 日本語を表示するための設定
        document.append(NoEscape(r"\begin{CJK}{UTF8}{ipxm}"))

        paragraphs = self.convert_paragraphs_to_latex(page.paragraphs, page.formulas)

        # ドキュメントにパラグラフを挿入
        for paragraph in paragraphs:
            if paragraph.role == "sectionHeading":
                self.paragraph_logger.debug(f"sectionHeading: {paragraph.content}")
                document = self.insert_section_heading_paragraph(paragraph, document)
            elif paragraph.role == "footnote":
                document = self.insert_footnote_paragraph(paragraph, document)
            elif paragraph.role == "pageHeader":
                document = self.insert_header_paragraph(paragraph, document)
            elif paragraph.role == "pageFooter":
                document = self.insert_footer_paragraph(paragraph, document)
            elif paragraph.role == "formulaBlock":
                continue
            else:
                document = self.insert_simple_paragraph(paragraph, document)

        # ドキュメントに数式を挿入
        for display_formula in page.display_formulas:
            document = self.insert_display_formula(display_formula, document)

        # ドキュメントに図を挿入
        for figure in page.figures:
            document = self.insert_figure(figure, document)

        # ドキュメントに表を挿入
        for table in page.tables:
            document = self.insert_table(table, document)

        document.append(NoEscape(r"\end{CJK}"))

        # ドキュメントをPDFに変換
        try:
            document.generate_pdf(output_path, clean_tex=False)
        except Exception as e:
            self.logger.warning(f"Error generating PDF: {e}")
            raise e

    def generate_pdf_with_translation(
        self, page: PageWithTranslation, output_path: str
    ):
        self.output_dir = os.path.dirname(output_path)
        geometry_options = {
            "margin": "0.0in",
            "paperwidth": f"{page.width}in",
            "paperheight": f"{page.height}in",
            "top": "0in",
            "bottom": "0in",
            "left": "0in",
            "right": "0in",
        }
        document = Document(geometry_options=geometry_options)
        document.packages.append(Package("textpos", options=["absolute"]))
        document.packages.append(Package("amsmath"))
        document.packages.append(Package("amssymb"))
        document.packages.append(Package("amsfonts"))
        document.packages.append(Package("graphicx"))
        document.packages.append(Package("tcolorbox", options=["fitting"]))
        document.packages.append(Package("CJK"))

        # 単位をインチに設定
        document.change_length(r"\TPHorizModule", "1in")
        document.change_length(r"\TPVertModule", "1in")

        # tcolorboxの設定
        document.append(
            NoEscape(
                r"""
            \tcbset{
                frame empty,  % 枠線なし
                interior empty,  % 背景なし
                boxsep=0pt,
                top=0pt,bottom=0pt,
                left=0pt,right=0pt,
                nobeforeafter,
                arc=0pt,
                outer arc=0pt,
                valign=center
            }
            """
            )
        )

        # 日本語を表示するための設定
        document.append(NoEscape(r"\begin{CJK}{UTF8}{ipxm}"))

        paragraphs = self.convert_paragraphs_with_translation_to_latex(
            page.paragraphs, page.formulas
        )

        for paragraph in paragraphs:
            if paragraph.role == "sectionHeading":
                document = self.insert_section_heading_paragraph(paragraph, document)
            elif paragraph.role == "footnote":
                document = self.insert_footnote_paragraph(paragraph, document)
            elif paragraph.role == "pageHeader":
                document = self.insert_header_paragraph(paragraph, document)
            elif paragraph.role == "pageFooter":
                document = self.insert_footer_paragraph(paragraph, document)
            elif paragraph.role == "formulaBlock":
                continue
            else:
                document = self.insert_simple_paragraph(paragraph, document)

        for display_formula in page.display_formulas:
            document = self.insert_display_formula(display_formula, document)

        for figure in page.figures:
            document = self.insert_figure(figure, document)

        for table in page.tables:
            document = self.insert_table(table, document)

        document.append(NoEscape(r"\end{CJK}"))

        try:
            document.generate_pdf(output_path, clean_tex=False)
        except Exception as e:
            self.logger.warning(f"Error generating PDF: {e}")
            raise e

    def generate_pdf_with_formula_id(self, page: PageWithTranslation, output_path: str):
        """
        PDFを生成する

        Args:
            page (PageWithTranslation): ページ
            output_path (str): 出力パス
        """
        self.output_dir = os.path.dirname(output_path)
        geometry_options = {
            "margin": "0.0in",
            "paperwidth": f"{page.width}in",
            "paperheight": f"{page.height}in",
            "top": "0in",
            "bottom": "0in",
            "left": "0in",
            "right": "0in",
        }
        document = Document(geometry_options=geometry_options)
        document.packages.append(Package("textpos", options=["absolute"]))
        document.packages.append(Package("amsmath"))
        document.packages.append(Package("amssymb"))
        document.packages.append(Package("amsfonts"))
        document.packages.append(Package("graphicx"))
        document.packages.append(Package("tcolorbox", options=["fitting"]))
        document.packages.append(Package("CJK"))

        # 単位をインチに設定
        document.change_length(r"\TPHorizModule", "1in")
        document.change_length(r"\TPVertModule", "1in")

        document.append(
            NoEscape(
                r"""
                \tcbset{
                    frame empty,  % 枠線なし
                    interior empty,  % 背景なし
                    boxsep=0pt,
                    top=0pt,bottom=0pt,
                    left=0pt,right=0pt,
                    nobeforeafter,
                    arc=0pt,
                    outer arc=0pt,
                    valign=center
                }
                """
            )
        )

        document.append(NoEscape(r"\begin{CJK}{UTF8}{ipxm}"))

        paragraphs = self.convert_paragraphs_with_formula_id_to_latex(
            page.paragraphs, page.formulas
        )

        for paragraph in paragraphs:
            if paragraph.role == "sectionHeading":
                document = self.insert_section_heading_paragraph(paragraph, document)
            elif paragraph.role == "footnote":
                document = self.insert_footnote_paragraph(paragraph, document)
            elif paragraph.role == "pageHeader":
                document = self.insert_header_paragraph(paragraph, document)
            elif paragraph.role == "pageFooter":
                document = self.insert_footer_paragraph(paragraph, document)
            elif paragraph.role == "formulaBlock":
                continue
            else:
                document = self.insert_simple_paragraph(paragraph, document)

        for display_formula in page.display_formulas:
            document = self.insert_display_formula(display_formula, document)

        for figure in page.figures:
            document = self.insert_figure(figure, document)

        for table in page.tables:
            document = self.insert_table(table, document)

        document.append(NoEscape(r"\end{CJK}"))

        if ".pdf" in output_path:
            output_basename = output_path.replace(".pdf", "")
        else:
            output_basename = output_path

        try:
            document.generate_pdf(
                output_basename,
                clean_tex=False,
                compiler_args=["-interaction=nonstopmode"],
            )
        except Exception as e:
            self.logger.warning(f"Error generating PDF: {e}")
            raise e

    def convert_paragraphs_to_latex(
        self, page_paragraphs: List[Paragraph], page_formulas: List[Formula]
    ) -> List[Paragraph]:
        """
        パラグラフをLaTeX形式に変換する

        Args:
            page_paragraphs (List[Paragraph]): ページのパラグラフのリスト
            page_formulas (List[Formula]): ページの数式のリスト

        Returns:
            List[Paragraph]: LaTeX形式に変換されたパラグラフのリスト
        """
        self.paragraph_logger.debug(f"--------------------------------")
        self.paragraph_logger.debug(
            f"page_paragraphs: {page_paragraphs} \npage_formulas: {page_formulas}"
        )
        self.paragraph_logger.debug(f"--------------------------------")
        current_formula_index = 0
        total_formulas = len(page_formulas)

        for paragraph in page_paragraphs:
            paragraph.content = escape_latex(paragraph.content)
            num_formula = paragraph.content.count(":formula:")
            if num_formula <= 0:
                continue

            self.paragraph_logger.debug(f"num_formula: {num_formula}")
            self.paragraph_logger.debug(
                f"paragraph before replace: {paragraph.content}"
            )

            for i in range(num_formula):
                if current_formula_index >= total_formulas:
                    self.logger.warning(
                        f"Not enough formulas ({total_formulas}) for all :formula: tokens in paragraphs"
                    )
                    break

                formula = page_formulas[current_formula_index]
                # もしformulaが不正なlatexの場合は警告する（eg. \begin{array}{}など）
                if r"\begin{array}{}" in formula.latex_value:
                    self.logger.warning(
                        f"Warning: Invalid LaTeX formula: {formula.latex_value}"
                    )
                    formula.latex_value = "??"
                paragraph.content = paragraph.content.replace(
                    f":formula:", f"${formula.latex_value}$", 1
                )
                current_formula_index += 1
            self.paragraph_logger.debug(f"paragraph after replace: {paragraph.content}")
            # もしまだ:formula:が残っていたらwarningを出す
            if ":formula:" in paragraph.content:
                self.paragraph_logger.warning(
                    f"Warning: :formula: is still in the paragraph: {paragraph.content}"
                )
        return page_paragraphs

    def convert_paragraphs_with_translation_to_latex(
        self,
        page_paragraphs_with_translation: List[ParagraphWithTranslation],
        page_formulas: List[Formula],
    ) -> List[Paragraph]:
        """
        翻訳されたパラグラフをLaTeX形式に変換する

        Args:
            page_paragraphs_with_translation (List[ParagraphWithTranslation]): 翻訳されたパラグラフのリスト

        Returns:
            List[Paragraph]: LaTeX形式に変換されたパラグラフのリスト
        """
        self.paragraph_logger.debug(f"--------------------------------")
        self.paragraph_logger.debug(
            f"page_paragraphs_with_translation: {page_paragraphs_with_translation}"
        )
        self.paragraph_logger.debug(f"--------------------------------")
        current_formula_index = 0
        total_formulas = len(page_formulas)
        paragraphs: List[Paragraph] = []

        for paragraph_with_translation in page_paragraphs_with_translation:
            paragraph_with_translation.translation = escape_latex(
                paragraph_with_translation.translation
            )
            num_formula = paragraph_with_translation.translation.count(":formula:")
            if num_formula <= 0:
                latex_paragraph = Paragraph(
                    paragraph_id=paragraph_with_translation.paragraph_id,
                    page_number=paragraph_with_translation.page_number,
                    content=paragraph_with_translation.translation,
                    role=paragraph_with_translation.role,
                    bbox=paragraph_with_translation.bbox,
                )
                paragraphs.append(latex_paragraph)
                continue
            self.paragraph_logger.debug(f"num_formula: {num_formula}")
            self.paragraph_logger.debug(
                f"paragraph before replace: {paragraph_with_translation.translation}"
            )

            for i in range(num_formula):
                if current_formula_index >= total_formulas:
                    self.logger.warning(
                        f"Not enough formulas ({total_formulas}) for all :formula: tokens in paragraphs"
                    )
                    break

                formula = page_formulas[current_formula_index]
                paragraph_with_translation.translation = (
                    paragraph_with_translation.translation.replace(
                        f":formula:", f"${formula.latex_value}$", 1
                    )
                )
                current_formula_index += 1
            self.paragraph_logger.debug(
                f"paragraph after replace: {paragraph_with_translation.translation}"
            )
            # もしまだ:formula:が残っていたらwarningを出す
            if ":formula:" in paragraph_with_translation.translation:
                self.paragraph_logger.warning(
                    f"Warning: :formula: is still in the paragraph: {paragraph_with_translation.translation}"
                )
            latex_paragraph = Paragraph(
                paragraph_id=paragraph_with_translation.paragraph_id,
                page_number=paragraph_with_translation.page_number,
                content=paragraph_with_translation.translation,
                role=paragraph_with_translation.role,
                bbox=paragraph_with_translation.bbox,
            )
            paragraphs.append(latex_paragraph)
        return paragraphs

    def convert_paragraphs_with_formula_id_to_latex(
        self,
        page_paragraphs_with_formula_id: List[ParagraphWithTranslation],
        page_formulas: List[Formula],
    ) -> List[Paragraph]:
        """
        パラグラフをLaTeX形式に変換する

        Args:
            page_paragraphs_with_formula_id (List[ParagraphWithTranslation]): パラグラフのリスト
            page_formulas (List[Formula]): 数式のリスト

        Returns:
            List[Paragraph]: LaTeX形式に変換されたパラグラフのリスト
        """
        self.paragraph_logger.debug(f"--------------------------------")
        self.paragraph_logger.debug(
            f"page_paragraphs_with_formula_id: {page_paragraphs_with_formula_id}"
        )
        self.paragraph_logger.debug(f"--------------------------------")
        total_formulas = len(page_formulas)
        paragraphs: List[Paragraph] = []
        formula_dict = {
            formula.formula_id: formula.latex_value for formula in page_formulas
        }
        formula_pattern = re.compile(r"<formula\\_(\d+)/>")
        for paragraph_with_formula_id in page_paragraphs_with_formula_id:
            paragraph_with_formula_id.translation = escape_latex(
                paragraph_with_formula_id.translation
            )
            # <formula_{formula_id}/>が含まれていたら
            formula_ids = formula_pattern.findall(paragraph_with_formula_id.translation)
            self.paragraph_logger.debug(f"Hit formula_ids: {formula_ids}")
            for formula_id in formula_ids:
                if int(formula_id) in formula_dict:
                    self.paragraph_logger.debug(f"Replace formula_id: {formula_id}")
                    # もしformula_latexが\begin{array}{}を含んでいたら、不正な数式として扱う
                    if r"\begin{array}{}" in formula_dict[int(formula_id)]:
                        formula_dict[int(formula_id)] = formula_dict[
                            int(formula_id)
                        ].replace(r"\begin{array}{}", r"\begin{array}{l}")
                    paragraph_with_formula_id.translation = (
                        paragraph_with_formula_id.translation.replace(
                            rf"<formula\_{formula_id}/>",
                            f"${formula_dict[int(formula_id)]}$",
                            1,
                        )
                    )
            self.paragraph_logger.debug(
                f"paragraph_with_formula_id.translation: {paragraph_with_formula_id.translation}"
            )
            latex_paragraph = Paragraph(
                paragraph_id=paragraph_with_formula_id.paragraph_id,
                page_number=paragraph_with_formula_id.page_number,
                content=paragraph_with_formula_id.translation,
                role=paragraph_with_formula_id.role,
                bbox=paragraph_with_formula_id.bbox,
            )
            paragraphs.append(latex_paragraph)
        return paragraphs

    def insert_simple_paragraph(
        self, paragraph: Paragraph, document: Document
    ) -> Document:
        """
        パラグラフを挿入する

        Args:
            paragraph (Paragraph): パラグラフ
            document (Document): ドキュメント

        Returns:
            Document: パラグラフが挿入されたドキュメント
        """
        bbox = paragraph.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        with document.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(
                    width=NoEscape(f"{width}in"),
                    height=NoEscape(f"{height}in"),
                    pos="t",
                )
            ) as mp:
                content = rf"\tcboxfit[height={height}in,width={width}in]{{{paragraph.content}}}"
                mp.append(NoEscape(content))
        return document

    def insert_display_formula(
        self, display_formula: DisplayFormula, document: Document
    ) -> Document:
        """
        数式を挿入する

        Args:
            display_formula (DisplayFormula): 数式
            document (Document): ドキュメント

        Returns:
            Document: 数式が挿入されたドキュメント
        """
        bbox = display_formula.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        if not display_formula.image_data:
            self.logger.warning(f"No image data found in display formula")
            return document

        # 画像を保存
        image_path = os.path.join(
            self.output_dir,
            f"formula_{display_formula.page_number}_{display_formula.formula_id}.png",
        )
        with open(image_path, "wb") as f:
            f.write(display_formula.image_data)

        with document.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(
                    width=NoEscape(f"{width}in"),
                    height=NoEscape(f"{height}in"),
                    pos="t",
                )
            ) as mp:
                content = rf"\includegraphics[width=\textwidth,height=\textheight,keepaspectratio]{{{image_path}}}"
                mp.append(NoEscape(content))
        return document

    def insert_section_heading_paragraph(
        self, section_heading_paragraph: Paragraph, document: Document
    ) -> Document:
        """セクション見出しパラグラフを挿入する

        Args:
            section_heading_paragraph (SectionHeadingParagraph): セクション見出しパラグラフ
            document (Document): ドキュメント

        Returns:
            Document: セクション見出しパラグラフが挿入されたドキュメント
        """
        bbox = section_heading_paragraph.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        with document.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(
                    width=NoEscape(f"{width}in"),
                    height=NoEscape(f"{height}in"),
                    pos="t",
                )
            ) as mp:
                # 太字で挿入する
                content = rf"\textbf{{{section_heading_paragraph.content}}}"
                mp.append(NoEscape(content))
        return document

    def insert_footnote_paragraph(
        self, footnote_paragraph: Paragraph, document: Document
    ) -> Document:
        """脚注パラグラフを挿入する

        Args:
            footnote_paragraph (Paragraph): 脚注パラグラフ
            document (Document): ドキュメント

        Returns:
            Document: 脚注パラグラフが挿入されたドキュメント
        """
        bbox = footnote_paragraph.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        with document.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(
                    width=NoEscape(f"{width}in"),
                    height=NoEscape(f"{height}in"),
                    pos="b",
                )
            ) as mp:
                mp.append(NoEscape(footnote_paragraph.content))
        return document

    def insert_header_paragraph(
        self, header_paragraph: Paragraph, document: Document
    ) -> Document:
        self.logger.debug(f"header_paragraph: {header_paragraph}")
        """ヘッダーパラグラフを挿入する

        Args:
            header_paragraph (Paragraph): ヘッダーパラグラフ
            document (Document): ドキュメント

        Returns:
            Document: ヘッダーパラグラフが挿入されたドキュメント
        """
        bbox = header_paragraph.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        content = escape_latex(header_paragraph.content)
        # ヘッダーの中央に配置
        with document.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(
                    width=NoEscape(f"{width}in"),
                    height=NoEscape(f"{height}in"),
                    pos="t",
                )
            ) as mp:
                mp.append(NoEscape(content))
        return document

    @staticmethod
    def insert_footer_paragraph(
        footer_paragraph: Paragraph, document: Document
    ) -> Document:
        """フッターパラグラフを挿入する"""
        bbox = footer_paragraph.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        content = escape_latex(footer_paragraph.content)
        # フッターの中央に配置
        with document.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(
                    width=NoEscape(f"{width}in"),
                    height=NoEscape(f"{height}in"),
                    pos="b",
                )
            ) as mp:
                mp.append(NoEscape(content))
        return document

    def insert_figure(self, figure: Figure, document: Document) -> Document:
        """図を挿入する

        Args:
            figure (Figure): 図
            document (Document): ドキュメント

        Returns:
            Document: 図が挿入されたドキュメント
        """
        bbox = figure.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        if not figure.image_data:
            self.logger.warning(f"No image data found in figure")
            return document

        # 画像を保存
        image_path = os.path.join(
            self.output_dir,
            f"figure_{figure.page_number}_{figure.figure_id}.png",
        )
        with open(image_path, "wb") as f:
            f.write(figure.image_data)

        with document.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(
                    width=NoEscape(f"{width}in"),
                    height=NoEscape(f"{height}in"),
                    pos="t",
                )
            ) as mp:
                content = rf"\includegraphics[width=\textwidth,height=\textheight,keepaspectratio]{{{image_path}}}"
                mp.append(NoEscape(content))
        return document

    def insert_table(self, table: Table, document: Document) -> Document:
        """表を挿入する

        Args:
            table (Table): 表
            document (Document): ドキュメント

        Returns:
            Document: 表が挿入されたドキュメント
        """
        bbox = table.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        if not table.image_data:
            self.logger.warning(f"No image data found in table")
            return document

        # 画像を保存
        image_path = os.path.join(
            self.output_dir,
            f"table_{table.page_number}_{table.table_id}.png",
        )
        with open(image_path, "wb") as f:
            f.write(table.image_data)

        with document.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(
                    width=NoEscape(f"{width}in"),
                    height=NoEscape(f"{height}in"),
                    pos="t",
                )
            ) as mp:
                content = rf"\includegraphics[width=\textwidth,height=\textheight,keepaspectratio]{{{image_path}}}"
                mp.append(NoEscape(content))
        return document
