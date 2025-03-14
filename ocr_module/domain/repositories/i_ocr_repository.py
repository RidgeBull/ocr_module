from abc import ABC, abstractmethod
from typing import List, Tuple

from ocr_module.domain.entities import (
    Document,
    Page,
    Section,
    OCRUsageStatsConfig,
)


class IOCRRepository(ABC):
    @abstractmethod
    def get_document(self, document_path: str) -> Tuple[Document, OCRUsageStatsConfig]:
        """
        ドキュメントを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Tuple[Document, OCRUsageStatsConfig]: ドキュメントの解析結果と使用統計情報
        """
        raise NotImplementedError

    @abstractmethod
    def get_pages(self, document_path: str) -> Tuple[List[Page], OCRUsageStatsConfig]:
        """
        ページを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            List[Page]: ページのリスト
        """
        raise NotImplementedError

    @abstractmethod
    def get_sections(self, document_path: str) -> Tuple[List[Section], OCRUsageStatsConfig]:
        """
        セクションを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            List[Section]: セクションのリスト
        """
        raise NotImplementedError
