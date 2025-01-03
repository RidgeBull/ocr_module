from abc import ABC, abstractmethod
from typing import List, Tuple

from ocr_module.domain.entities import Page, PageWithTranslation


class IPDFGeneratorRepository(ABC):
    @abstractmethod
    def generate_pdf(
        self,
        page: Page,
        output_path: str,
    ):
        """
        PDFを生成する

        Args:
            page (Page): ページ
            output_path (str): 出力パス
        """
        raise NotImplementedError

    @abstractmethod
    def generate_pdf_with_translation(
        self,
        page: PageWithTranslation,
        output_path: str,
    ):
        """
        PDFを生成する

        Args:
            page (PageWithTranslation): ページ
            output_path (str): 出力パス
        """
        raise NotImplementedError

    @abstractmethod
    def generate_pdf_with_formula_id(
        self,
        page: PageWithTranslation,
        output_path: str,
    ):
        """
        PDFを生成する

        Args:
            page (PageWithTranslation): ページ
            output_path (str): 出力パス
        """
        raise NotImplementedError
