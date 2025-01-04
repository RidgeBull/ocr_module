import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger
from typing import List
import copy

from ocr_module.domain.entities import PageWithTranslation
from ocr_module.domain.repositories import IPDFGeneratorRepository
from PyPDF2 import PdfMerger


class GenerateTranslatedPDFWithFormulaIdUseCase:
    def __init__(
        self,
        pdf_generator_repository: IPDFGeneratorRepository,
        error_pdf_generator_repository: IPDFGeneratorRepository,
        max_workers: int = 10,
    ):
        self.pdf_generator_repository = pdf_generator_repository
        self.error_pdf_generator_repository = error_pdf_generator_repository
        self.max_workers = max_workers
        self.logger = getLogger(__name__)

    def _process_page(
        self,
        page_with_translation: PageWithTranslation,
        output_path: str,
    ) -> str:
        """1ページを処理する

        Args:
            page_with_translation (PageWithTranslation): 翻訳されたページ
            output_path (str): documentの出力パス. pageの出力パスは `{output_path.replace(".pdf", "")}_{page_number}.pdf` というパスになる

        Returns:
            str: pageの出力パス (.pdfを含む)
        """
        doc_prefix = output_path.replace(".pdf", "")
        page_output_path = f"{doc_prefix}_{page_with_translation.page_number}.pdf"
        try:
            page_copy = copy.deepcopy(page_with_translation)
            self.pdf_generator_repository.generate_pdf_with_formula_id(
                page=page_copy, output_path=page_output_path
            )
            return page_output_path
        except Exception as e:
            self.logger.warning(
                f"Error compiling page {page_with_translation.page_number}: {e}"
                f"Generating error PDF"
            )
            # TODO: エラー処理適切にしたい。空ページか、エラーが発生したのでPDF化できませんでした、という文言のPDFを出すか
            raise e

    def _merge_pdfs(self, pdf_paths: List[str], output_path: str) -> str:
        """PDFを結合する"""
        merger = PdfMerger()
        for pdf_path in sorted(
            pdf_paths, key=lambda x: int(x.split("_")[-1].replace(".pdf", ""))
        ):
            merger.append(pdf_path)

        if ".pdf" in output_path:
            output_basename = output_path.replace(".pdf", "")
        else:
            output_basename = output_path

        final_path = f"{output_basename}.pdf"
        merger.write(final_path)
        merger.close()

        return final_path

    def _remove_page_pdf(self, pdf_paths: List[str]) -> None:
        # 一時ファイルを削除
        for pdf_path in pdf_paths:
            try:
                os.remove(pdf_path)
            except Exception as e:
                self.logger.warning(f"Failed to remove temporary file {pdf_path}: {e}")

    def execute(
        self,
        pages_with_translations: List[PageWithTranslation],
        output_path: str,
        save_page_file: bool = False,
    ) -> tuple[str, list[str]]:
        """
        ページごとに翻訳を行い、PDFを生成する

        Args:
            pages_with_translations (List[PageWithTranslation]): 翻訳されたページのリスト
            output_path (str): 出力パス.
            save_page_file (bool, optional): ページごとのPDFを保存するかどうか. デフォルトはFalse.
              ページごとのPDFは `{output_path}_{page_number}.pdf` というパスに保存される

        Returns:
            tuple[str, list[str]]: 結合されたPDFのパス, ページごとのPDFのパスのリスト
        """
        page_pdf_paths = []

        # 並列処理でページを処理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_page = {
                executor.submit(self._process_page, page, output_path): page
                for page in pages_with_translations
            }

            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    page_pdf_path = future.result()
                    page_pdf_paths.append(page_pdf_path)
                    self.logger.info(f"Completed processing page {page.page_number}")
                except Exception as e:
                    self.logger.warning(
                        f"Failed to process page {page.page_number}: {e}"
                    )
                    page_output_path = f"{output_path.replace('.pdf', '')}_{page.page_number}_error.pdf"
                    self.error_pdf_generator_repository.generate_pdf_with_translation(
                        page=page, output_path=page_output_path
                    )
                    page_pdf_paths.append(page_output_path)
        # すべてのPDFを結合
        if not page_pdf_paths:
            raise Exception("No pages were successfully processed")

        final_path = self._merge_pdfs(page_pdf_paths, output_path)
        self.logger.info(f"Successfully created merged PDF at {final_path}")

        # 中間ファイルを保存しない場合、ページごとのPDFを削除
        if not save_page_file:
            self._remove_page_pdf(page_pdf_paths)

        return final_path, page_pdf_paths
