import logging
import os
import subprocess
from logging import getLogger
from typing import Dict, List, Tuple

from pylatex import Command, Document, MiniPage, TextBlock
from pylatex.package import Package
from pylatex.utils import NoEscape, escape_latex

from ocr_module.domain.entities import (
    DisplayFormula,
    Figure,
    Section,
    SectionWithTranslation,
    Table,
    TextParagraph,
    TextParagraphWithTranslation,
)
from ocr_module.domain.repositories import IPDFGeneratorRepository


class PyLaTeXGeneratePDFRepository(IPDFGeneratorRepository):
    def __init__(self):
        self.logger = getLogger(__name__)
        self.paragraph_logger = getLogger("paragraph")
        # すでに設定されているハンドラを削除して、新しいハンドラを設定してファイルに出力する
        for handler in self.paragraph_logger.handlers:
            self.paragraph_logger.removeHandler(handler)
        # modeを'w'に設定して上書きモードにする
        handler = logging.FileHandler("paragraph.log", mode="w")
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.paragraph_logger.addHandler(handler)
        # ログレベルをDEBUGに設定
        self.paragraph_logger.setLevel(logging.INFO)
        geometry_options = {"margin": "0.0in"}
        self.doc = Document(indent=False, geometry_options=geometry_options)

        # 必要最小限のパッケージに絞る
        essential_packages = [
            ("textpos", None),
            ("amsmath", None),
            ("CJK", None),
            ("graphicx", None),
            ("tcolorbox", ["fitting"]),
        ]

        for package, options in essential_packages:
            self.doc.packages.append(Package(package, options=options))

        # 単位をインチに設定
        self.doc.change_length(r"\TPHorizModule", "1in")
        self.doc.change_length(r"\TPVertModule", "1in")

        # 日本語を表示するための設定
        self.doc.append(NoEscape(r"\begin{CJK}{UTF8}{ipxm}"))

        self.temp_files = []  # 一時ファイルを追跡

    def _set_page_size(self, page_size: Tuple[float, float]) -> Document:
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
        return self.doc

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
        self.output_dir = os.path.dirname(output_path)
        self.doc = self._set_page_size(page_size)
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
                    # そページの数式リストを取得（数式がない場合は空リスト）
                    page_formulas = formula_dict.get(page_number, [])
                    self._insert_page(
                        page_dict[page_number],
                        page_formulas,
                        figure_dict.get(page_number, []),
                        table_dict.get(page_number, []),
                        page_number,
                    )
                else:
                    self.logger.debug(f"Page {page_number} has no content.")

            # 日本語を表示するための設定
            self.doc.append(NoEscape(r"\end{CJK}"))

            self.logger.debug(f"Generated LaTeX code: {self.doc.dumps()}")

            # PDF を保存
            try:
                self.doc.generate_pdf(
                    output_path,
                    clean_tex=False,
                    compiler="pdflatex",
                    compiler_args=[
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        "-file-line-error",
                        "-shell-escape",
                    ],
                )
                self.logger.debug(f"PDF generated successfully at {output_path}")
            except subprocess.CalledProcessError as e:
                self.logger.error(
                    f"LaTeX compilation error: {e.output.decode('utf-8') if e.output else str(e)}"
                )
                raise

        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {str(e)}")
            raise

        finally:
            # 一時ファイルの削除
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to remove temporary file {temp_file}: {e}"
                    )
            self.temp_files.clear()

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

    def _group_tables_by_page(self, sections: List[Section]) -> Dict[int, List[Table]]:
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
            self.logger.debug(f"Inserting paragraph: {paragraph.text}")
            self._insert_paragraph(paragraph)

        # 数式の挿入（数式リストが空の場合はスキップされる）
        for idx, formula in enumerate(formulas):
            self.logger.debug(f"Inserting formula: {formula.latex_value}")
            self._insert_formula(formula, page_number, idx)

        # 図の挿入
        for idx, figure in enumerate(figures):
            self.logger.debug(f"Inserting figure: {figure.image_data}")
            self._insert_figure(figure, idx, page_number)

        # テーブルの挿入
        for idx, table in enumerate(tables):
            self.logger.debug(f"Inserting table: {table.image_data}")
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

    def _insert_formula(self, formula: DisplayFormula, page_number: int, idx: int):
        """
        数式を指定された位置に挿入。
        """
        bbox = formula.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        # 画像を挿入する
        temp_image_path = os.path.join(
            self.output_dir, f"temp_formula_{page_number}_{idx}.png"
        )
        self.temp_files.append(temp_image_path)  # 一時ファイルを追跡

        if formula.image_data is None:
            self.logger.error("No image data found in formula")
            return

        try:
            with open(temp_image_path, "wb") as f:
                f.write(formula.image_data)
            self.logger.debug(f"Temporary image saved to: {temp_image_path}")
            with self.doc.create(TextBlock(width, x, y)) as block:
                block.append(
                    NoEscape(
                        rf"\includegraphics[width=\textwidth,height=\textheight,keepaspectratio]{{{temp_image_path}}}"
                    )
                )
        except Exception as e:
            self.logger.error(f"Failed to save temporary image: {e}")
            return

    def _insert_figure(self, figure: Figure, idx: int, page_number: int):
        """画像を指定された位置に挿入"""
        self.logger.debug(f"Attempting to insert figure with bbox: {figure.bbox}")

        if not figure.image_data:
            self.logger.warning("No image data found in figure")
            return

        bbox = figure.bbox
        x = bbox[0]
        y = bbox[1]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        # 一時ファイルのパスを絶対パスで指定
        temp_image_path = os.path.join(
            self.output_dir, f"temp_figure_{page_number}_{idx}.png"
        )
        self.temp_files.append(temp_image_path)  # 一時ファイルを追跡

        try:
            # 画像データを保存
            with open(temp_image_path, "wb") as f:
                f.write(figure.image_data)
            self.logger.debug(f"Temporary image saved to: {temp_image_path}")

            # TextBlockを作成して画像を配置
            with self.doc.create(TextBlock(width, x, y)) as block:
                # 画像を挿入（サイズ指定を修正）
                block.append(
                    NoEscape(
                        rf"\includegraphics[width=\textwidth,height=\textheight,keepaspectratio]{{{temp_image_path}}}"
                    )
                )
            self.logger.debug("Successfully inserted figure into document")

        except Exception as e:
            self.logger.error(f"Failed to insert figure: {e}")
            return

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
        self.temp_files.append(temp_image_path)  # 一時ファイルを追跡
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

        # 数式から余分なカンマを除去
        formulas = [f.rstrip(" ,") for f in paragraph.inline_formulas]

        # 含まれる:formula:の数とinline_formulasの数を比較
        formula_count = text.count(":formula:")
        if formula_count != len(formulas):
            self.paragraph_logger.warning(
                f"formula_count: {formula_count}, formulas: {formulas}\n"
                f"text: {text}\n"
            )

        # すべての数式を一度に置換
        for formula in formulas:
            if "\\begin{array}{}" in formula:
                formula = formula.replace("\\begin{array}{}", "\\begin{array}{l}")

            # 数式を$で囲む
            math_expr = f"${formula}$"
            # 最初に見つかった:formula:を置換
            text = text.replace(":formula:", math_expr, 1)

        self.paragraph_logger.debug(f"text: {text}")

        return text
