from pylatex import Document, TextBlock, MiniPage, Command
from pylatex.package import Package
from pylatex.utils import escape_latex, NoEscape
from logging import getLogger
from typing import List, Dict
from ocr.domain.entities import Section, TextParagraph, DisplayFormula
from ocr.domain.repositories import IPDFGeneratorRepository


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

    def generate_pdf(
        self,
        sections: List[Section],
        page_num: int,
        output_path: str,
        display_formulas: List[DisplayFormula],
    ):
        """
        セクションリストを受け取り、PDFを生成して保存する。
        """
        try:
            # ページ番号ごとにパラグラフをグループ化
            page_dict = self._group_paragraphs_by_page(sections)

            # ページ番号ごとに数式をグループ化
            formula_dict = self._group_formulas_by_page(display_formulas)

            # 各ページに挿入
            for page_number in range(1, page_num + 1):
                if page_number in page_dict:
                    # そのページの数式リストを取得（数式がない場合は空リスト）
                    page_formulas = formula_dict.get(page_number, [])
                    self._insert_page(page_dict[page_number], page_formulas)
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
        self, sections: List[Section]
    ) -> Dict[int, List[TextParagraph]]:
        """
        セクションをページ番号ごとにグループ化する。
        """
        page_dict = {}
        for section in sections:
            for paragraph in section.paragraphs:
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

    def _insert_page(
        self, paragraphs: List[TextParagraph], formulas: List[DisplayFormula]
    ):
        """
        ページにパラグラフと数式を挿入。
        """
        # パラグラフの挿入
        for paragraph in paragraphs:
            self._insert_paragraph(paragraph)

        # 数式の挿入（数式リストが空の場合はスキップされる）
        for formula in formulas:
            self._insert_formula(formula)

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
                mp.append(
                    NoEscape(
                        rf"\[{formula.latex_value}\]"
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
