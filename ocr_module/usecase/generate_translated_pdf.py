import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger
from typing import List

from PyPDF2 import PdfMerger

from ocr_module.domain.entities import PageWithTranslation
from ocr_module.domain.repositories import IPDFGeneratorRepository


class GenerateTranslatedPdfUseCase:
    def __init__(
        self, pdf_generator_repository: IPDFGeneratorRepository, max_workers: int = 4
    ):
        self.logger = getLogger(__name__)
        self.pdf_generator_repository = pdf_generator_repository
        self.max_workers = max_workers

    def _process_page(
        self, page_with_translation: PageWithTranslation, base_output_path: str
    ) -> str:
        """1ページを処理する"""
        page_output_path = f"{base_output_path}_{page_with_translation.page_number}"
        try:
            self.pdf_generator_repository.generate_pdf_with_translation(
                page_with_translation, page_output_path
            )
            return f"{page_output_path}.pdf"
        except Exception as e:
            self.logger.error(
                f"Error processing page {page_with_translation.page_number}: {e}"
            )
            raise

    def _merge_pdfs(self, pdf_paths: List[str], output_path: str) -> str:
        """PDFを結合する"""
        merger = PdfMerger()
        for pdf_path in sorted(
            pdf_paths, key=lambda x: int(x.split("_")[-1].replace(".pdf", ""))
        ):
            merger.append(pdf_path)

        final_path = f"{output_path}.pdf"
        merger.write(final_path)
        merger.close()

        # 一時ファイルを削除
        for pdf_path in pdf_paths:
            try:
                os.remove(pdf_path)
            except Exception as e:
                self.logger.warning(f"Failed to remove temporary file {pdf_path}: {e}")

        return final_path

    def execute(
        self, page_with_translations: List[PageWithTranslation], output_path: str
    ) -> str:
        """
        翻訳付きPDFを生成し、結合されたPDFのパスを返す

        Args:
            page_with_translations (List[PageWithTranslation]): 翻訳付きページリスト
            output_path (str): 出力PDFのベースパス

        Returns:
            str: 結合されたPDFのパス
        """
        pdf_paths = []

        # 並列処理でページを処理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_page = {
                executor.submit(self._process_page, page, output_path): page
                for page in page_with_translations
            }

            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    pdf_path = future.result()
                    pdf_paths.append(pdf_path)
                    self.logger.debug(f"Completed processing page {page.page_number}")
                except Exception as e:
                    self.logger.error(f"Failed to process page {page.page_number}: {e}")

        # すべてのPDFを結合
        if not pdf_paths:
            raise Exception("No pages were successfully processed")

        final_path = self._merge_pdfs(pdf_paths, output_path)
        self.logger.debug(f"Successfully created merged PDF at {final_path}")

        return final_path
