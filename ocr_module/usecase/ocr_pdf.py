import copy
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger
from typing import List

from PyPDF2 import PdfMerger

from ocr_module.domain.entities import Page
from ocr_module.domain.repositories import IOCRRepository, IPDFGeneratorRepository


class OCRPDFUseCase:
    def __init__(
        self,
        ocr_repository: IOCRRepository,
        pdf_repository: IPDFGeneratorRepository,
        max_workers: int = 4,
    ):
        self.ocr_repository = ocr_repository
        self.pdf_repository = pdf_repository
        self.max_workers = max_workers
        self.logger = getLogger(__name__)
        for handler in self.logger.handlers:
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
        self.logger.addHandler(logging.FileHandler("ocr_pdf.log", mode="w"))
        self.logger.setLevel(logging.INFO)

    def _process_page(self, page: Page, base_output_path: str) -> str:
        """1ページを処理する"""
        page_output_path = f"{base_output_path}_{page.page_number}"
        try:
            page_copy = copy.deepcopy(page)
            self.pdf_repository.generate_pdf(page_copy, page_output_path)
            return f"{page_output_path}.pdf"
        except Exception as e:
            self.logger.error(f"Error processing page {page.page_number}: {e}")
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

    def execute(self, document_path: str, output_path: str) -> List[Page]:
        """
        PDFをOCR処理し、結合されたPDFを生成する

        Args:
            document_path (str): 入力PDFのパス
            output_path (str): 出力PDFのベースパス

        Returns:
            List[Page]: ページのリスト
        """
        original_pages = self.ocr_repository.get_pages(document_path)
        self.logger.info(f"Original pages: {original_pages}")
        pdf_paths = []

        # 並列処理でページを処理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_page = {
                executor.submit(self._process_page, page, output_path): page
                for page in original_pages
            }

            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    pdf_path = future.result()
                    pdf_paths.append(pdf_path)
                    self.logger.info(f"Completed processing page {page.page_number}")
                except Exception as e:
                    self.logger.error(f"Failed to process page {page.page_number}: {e}")

        # すべてのPDFを結合
        if not pdf_paths:
            raise Exception("No pages were successfully processed")

        final_path = self._merge_pdfs(pdf_paths, output_path)
        self.logger.info(f"Successfully created merged PDF at {final_path}")
        self.logger.info(f"Original pages: {original_pages}")

        return original_pages
