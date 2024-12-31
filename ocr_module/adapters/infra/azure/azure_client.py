import os
import time
from typing import List

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    AnalyzeResult,
    DocumentAnalysisFeature,
)
from azure.core.credentials import AzureKeyCredential

from config import settings


class AzureDocumentIntelligenceClient:
    def __init__(
        self,
        endpoint: str = settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
        key: str = settings.AZURE_DOCUMENT_INTELLIGENCE_KEY,
    ):
        """
        Azure Document Intelligence クライアントの初期化

        Args:
            endpoint (str, optional): Azure Document Intelligence エンドポイント. Defaults to settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT.
            key (str, optional): Azure Document Intelligence キー. Defaults to settings.AZURE_DOCUMENT_INTELLIGENCE_KEY.
        """
        self.endpoint = endpoint
        self.key = key
        self.client: DocumentIntelligenceClient = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key),
        )

    def set_features(self, features: List[DocumentAnalysisFeature]):
        """
        クライアントに使用する機能を設定

        Args:
            features (List[DocumentAnalysisFeature]): 使用する機能のリスト
        """
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key),
            features=features,
        )

    def analyze_document_from_document_path(self, document_path: str) -> AnalyzeResult:
        """
        ドキュメントを分析

        Args:
            document_path (str): 分析するドキュメントのパス
        """
        document_bytes = open(document_path, "rb").read()
        return self.analyze_document_from_bytes(document_bytes)

    def analyze_document_from_bytes(self, document_bytes: bytes) -> AnalyzeResult:
        """
        ドキュメントを分析

        Args:
            document_bytes (bytes): 分析するドキュメントのバイト列
        """
        poller = self.client.begin_analyze_document(
            "prebuilt-layout",
            AnalyzeDocumentRequest(bytes_source=document_bytes),
            features=[
                DocumentAnalysisFeature.FORMULAS,
                DocumentAnalysisFeature.STYLE_FONT,
            ],
        )
        while not poller.done():
            print("Waiting for result...")
            time.sleep(5)
        if poller.status() == "failed":
            print("Failed!")
            raise Exception("Failed to analyze document")
        else:
            print("Done!")
            result: AnalyzeResult = poller.result()
            print("Result is ready!")
            with open(
                os.path.join(os.path.dirname(document_path), "result.json"), "w"
            ) as f:
                f.write(result.__str__())
            return result

    def analyze_document_from_url(self, document_url: str) -> AnalyzeResult:
        """
        ドキュメントを分析

        Args:
            document_url (str): 分析するドキュメントのURL
        """
        poller = self.client.begin_analyze_document(
            "prebuilt-layout",
            AnalyzeDocumentRequest(url_source=document_url),
            features=[
                DocumentAnalysisFeature.FORMULAS,
                DocumentAnalysisFeature.STYLE_FONT,
            ],
        )
        while not poller.done():
            print("Waiting for result...")
            time.sleep(5)
        result: AnalyzeResult = poller.result()
        return result
