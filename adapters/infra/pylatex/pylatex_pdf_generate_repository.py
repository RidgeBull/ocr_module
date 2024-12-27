from pylatex import Document, TextBlock, MiniPage, Command
from pylatex.package import Package
from pylatex.utils import escape_latex, NoEscape
from logging import getLogger
from typing import List, Dict, Tuple
from ocr.domain.entities import (
    Section,
    SectionWithTranslation,
    TextParagraph,
    DisplayFormula,
    Figure,
    TextParagraphWithTranslation,
    Table,
)
from ocr.domain.repositories import IPDFGeneratorRepository
import os


class PyLaTeXGeneratePDFRepository(IPDFGeneratorRepository):
    def __init__(self):
        self.logger = getLogger(__name__)
        geometry_options = {"margin": "0.0in"}
        self.doc = Document(indent=False, geometry_options=geometry_options)

        # 必要なパッケージを追加
        self.doc.packages.append(Package("textpos"))
        self.doc.packages.append(Package("amsmath"))
        self.doc.packages.append(Package("amssymb"))
        self.doc.packages.append(Package("amsfonts"))
        self.doc.packages.append(Package("CJK"))
        self.doc.packages.append(Package("adjustbox"))
        self.doc.packages.append(Package("graphicx"))
        # tcolorboxとその設定を追加
        self.doc.packages.append(
            Package("tcolorbox", options=["fitting"])
        )  # fittingライブラリをオプションとして追加

        # tcolorboxの設定
        self.doc.append(
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

        # 単位をインチに設定
        self.doc.change_length(r"\TPHorizModule", "1in")
        self.doc.change_length(r"\TPVertModule", "1in")

        # 日本語を表示するための設定
        self.doc.append(NoEscape(r"\begin{CJK}{UTF8}{ipxm}"))

    def _set_page_size(self, page_size: Tuple[float, float]):
        width, height = page_size
        geometry_options = {
            "margin": "0.0in",
            "paperwidth": f"{width}in",
            "paperheight": f"{height}in",
            "top": "0in",
            "bottom": "0in",
            "left": "0in",
            "right": "0in",
        }
        self.doc = Document(indent=False, geometry_options=geometry_options)
        self.doc.packages.append(Package("textpos"))
        self.doc.packages.append(Package("amsmath"))
        self.doc.packages.append(Package("amssymb"))
        self.doc.packages.append(Package("amsfonts"))
        self.doc.packages.append(Package("CJK"))
        self.doc.packages.append(Package("adjustbox"))
        self.doc.packages.append(Package("graphicx"))

        # tcolorboxとその設定を追加
        self.doc.packages.append(
            Package("tcolorbox", options=["fitting"])
        )  # fittingライブラリをオプションとして追加

        # tcolorboxの設定
        self.doc.append(
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

        # 単位をインチに設定
        self.doc.change_length(r"\TPHorizModule", "1in")
        self.doc.change_length(r"\TPVertModule", "1in")

        # 日本語を表示するための設定
        self.doc.append(NoEscape(r"\begin{CJK}{UTF8}{ipxm}"))

    def generate_pdf(
        self,
        sections: List[Section],
        page_num: int,
        output_path: str,
        display_formulas: List[DisplayFormula],
        page_size: Tuple[float, float],  # (width, height)
    ):
        """
        セクションリストを受け取り、PDFを生成して保存する。
        """
        width, height = page_size
        self._set_page_size(page_size)
        self.output_dir = os.path.dirname(output_path)

        try:
            # ページ番号ごとにパラグラフをグループ化
            page_dict = self._group_paragraphs_by_page(
                [paragraph for section in sections for paragraph in section.paragraphs]
            )

            # ページ番号ごとに数式をグループ化
            formula_dict = self._group_formulas_by_page(display_formulas)

            # figureをグループ化
            figure_dict = self._group_figures_by_page(sections)

            # tableをグループ化
            table_dict = self._group_tables_by_page(sections)

            # 各ページに挿入
            for page_number in range(1, page_num + 1):
                if page_number in page_dict:
                    # そのページの数式リストを取得（数式がない場合は空リスト）
                    page_formulas = formula_dict.get(page_number, [])
                    self._insert_page(
                        page_dict[page_number],
                        page_formulas,
                        figure_dict.get(page_number, []),
                        table_dict.get(page_number, []),
                        page_number,
                    )
                else:
                    self.logger.info(f"Page {page_number} has no content.")

            # 日本語を表示するための設定
            self.doc.append(NoEscape(r"\end{CJK}"))

            # PDF を保存
            self.doc.generate_pdf(output_path, clean_tex=False)
            self.logger.info(f"PDF generated successfully at {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {e}")
            raise

    def _group_paragraphs_by_page(
        self, paragraphs: List[TextParagraph]
    ) -> Dict[int, List[TextParagraph]]:
        """
        セクションをページ番号ごとにグループ化する。
        """
        page_dict = {}
        for paragraph in paragraphs:
            if paragraph.page_number not in page_dict:
                page_dict[paragraph.page_number] = []
            page_dict[paragraph.page_number].append(paragraph)
        return page_dict

    def _group_formulas_by_page(
        self, display_formulas: List[DisplayFormula]
    ) -> Dict[int, List[DisplayFormula]]:
        """
        数式をページ番号ごとにグループ化する。
        """
        formula_dict = {}
        for formula in display_formulas:
            if formula.page_number not in formula_dict:
                formula_dict[formula.page_number] = []
            formula_dict[formula.page_number].append(formula)
        return formula_dict

    def _group_figures_by_page(
        self, sections: List[Section]
    ) -> Dict[int, List[Figure]]:
        """
        図をページ番号ごとにグループ化する。
        """
        figure_dict = {}
        for section in sections:
            for figure in section.figures:
                if figure.page_number not in figure_dict:
                    figure_dict[figure.page_number] = []
                figure_dict[figure.page_number].append(figure)
        return figure_dict

    def _group_tables_by_page(
        self, sections: List[Section]
    ) -> Dict[int, List[Table]]:
        """
        テーブルをページ番号ごとにグループ化する。
        """
        table_dict = {}
        for section in sections:
            for table in section.tables:
                if table.page_number not in table_dict:
                    table_dict[table.page_number] = []
                table_dict[table.page_number].append(table)
        return table_dict

    def _insert_page(
        self,
        paragraphs: List[TextParagraph],
        formulas: List[DisplayFormula],
        figures: List[Figure],
        tables: List[Table],
        page_number: int,
    ):
        """
        ページにパラグラフと数式を挿入。
        """
        self.logger.debug(
            f"Inserting page with {len(paragraphs)} paragraphs and {len(formulas)} formulas"
        )

        # パラグラフの挿入
        for paragraph in paragraphs:
            self._insert_paragraph(paragraph)

        # 数式の挿入（数式リストが空の場合はスキップされる）
        for formula in formulas:
            self._insert_formula(formula)

        # 図の挿入
        for idx, figure in enumerate(figures):
            self._insert_figure(figure, idx, page_number)

        # テーブルの挿入
        for idx, table in enumerate(tables):
            self._insert_table(table, idx, page_number)

        # 新しいページを作成
        self.doc.append(NoEscape(r"\newpage"))

    def _insert_paragraph(self, paragraph: TextParagraph):
        """
        パラグラフを指定された位置に挿入。テキストが矩形内に収まるように自動でサイズ調整。
        """
        bbox = paragraph.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        text_content = self._sanitize_paragraph_text(paragraph)

        # TextBlock を作成して文章を配置
        with self.doc.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(width=NoEscape(f"{width}in"), height=NoEscape(f"{height}in"))
            ) as mp:
                # tcolorboxを使用してテキストを配置
                content = (
                    rf"\tcboxfit[height={height}in,width={width}in]{{{text_content}}}"
                )
                mp.append(NoEscape(content))

    def _insert_formula(self, formula: DisplayFormula):
        """
        数式を指定された位置に挿入。
        """
        bbox = formula.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        with self.doc.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(width=NoEscape(f"{width}in"), height=NoEscape(f"{height}in"))
            ) as mp:
                mp.append(NoEscape(rf"\[{formula.latex_value}\]"))

    def _insert_figure(self, figure: Figure, idx: int, page_number: int):
        """
        画像を指定された位置に挿入
        """
        self.logger.debug(f"Attempting to insert figure with bbox: {figure.bbox}")

        if not figure.image_data:
            self.logger.warning("No image data found in figure")
            return

        bbox = figure.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        self.logger.debug(
            f"Figure dimensions: x={x}, y={y}, width={width}, height={height}"
        )

        # 画像を一時ファイルとして保存
        temp_image_path = os.path.join(
            self.output_dir, f"temp_figure_{page_number}_{idx}.png"
        )
        try:
            with open(temp_image_path, "wb") as f:
                f.write(figure.image_data)
            self.logger.debug(f"Temporary image saved to: {temp_image_path}")
        except Exception as e:
            self.logger.error(f"Failed to save temporary image: {e}")
            return

        # TextBlockを作成して画像を配置
        try:
            with self.doc.create(TextBlock(width, x, y)) as block:
                with block.create(
                    MiniPage(
                        width=NoEscape(f"{width}in"), height=NoEscape(f"{height}in")
                    )
                ) as mp:
                    # 画像を挿入（アスペクト比を保持）
                    mp.append(
                        NoEscape(
                            r"\includegraphics[width=\linewidth,height=\linewidth,keepaspectratio]"
                            f"{{{temp_image_path}}}"
                        )
                    )
            self.logger.debug("Successfully inserted figure into document")
        except Exception as e:
            self.logger.error(f"Failed to insert figure into document: {e}")

        # # キャプションがある場合は追加
        # if figure.caption and figure.caption.content:
        #     self.logger.debug(f"Adding caption: {figure.caption.content}")
        #     caption_bbox = figure.caption.bbox
        #     caption_x = caption_bbox[0]
        #     caption_y = caption_bbox[1]
        #     caption_width = caption_bbox[2] - caption_bbox[0]

        #     try:
        #         with self.doc.create(
        #             TextBlock(caption_width, caption_x, caption_y)
        #         ) as block:
        #             block.append(figure.caption.content)
        #         self.logger.debug("Successfully added caption")
        #     except Exception as e:
        #         self.logger.error(f"Failed to add caption: {e}")

    def _insert_table(self, table: Table, idx: int, page_number: int):
        """
        テーブルを指定された位置に挿入

        Args:
            table (Table): テーブル
            idx (int): テーブルのインデックス
            page_number (int): ページ番号
        """
        self.logger.debug(f"Attempting to insert table with bbox: {table.bbox}")
        if not table.image_data:
            self.logger.warning("No image data found in table")
            return
        bbox = table.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        self.logger.debug(
            f"Table dimensions: x={x}, y={y}, width={width}, height={height}"
        )

        # 画像を一時ファイルとして保存する
        temp_image_path = os.path.join(
            self.output_dir, f"temp_table_{page_number}_{idx}.png"
        )
        try:
            with open(temp_image_path, "wb") as f:
                f.write(table.image_data)
            self.logger.debug(f"Temporary image saved to: {temp_image_path}")
        except Exception as e:
            self.logger.error(f"Failed to save temporary image: {e}")
            return

        with self.doc.create(TextBlock(width, x, y)) as block:
            with block.create(
                MiniPage(width=NoEscape(f"{width}in"), height=NoEscape(f"{height}in"))
            ) as mp:
                # テーブル画像を挿入
                mp.append(
                    NoEscape(
                        rf"\includegraphics[width=\linewidth,height=\linewidth,keepaspectratio]{{{temp_image_path}}}"
                    )
                )

    def _sanitize_paragraph_text(self, paragraph: TextParagraph) -> str:
        """
        パラグラフのテキストをエスケープし、数式を置換。
        """
        text = escape_latex(paragraph.text)  # テキスト部分をエスケープ
        for formula in paragraph.inline_formulas:
            text = text.replace(":formula:", f"${formula}$", 1)  # 数式部分を置換
        return text
