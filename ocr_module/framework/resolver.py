from ..adapters.infra.azure import (
    AzureOCRRepository,
    AzureOpenAITranslateSectionRepository,
)
from ..adapters.infra.deepl import DeepLTranslateSectionRepository
from ..adapters.infra.openai import OpenAITranslateSectionRepository
from ..adapters.infra.pylatex import PyLaTeXGeneratePDFRepository
from ..adapters.infra.pymupdf import PyMuPDFGeneratePDFRepository, PyMuPDFImageExtractor
from ..domain.entities import Document, PageWithTranslation, TranslatedDocument
from ..usecase import (
    ChangeFormulaIdUseCase,
    GenerateTranslatedPDFWithFormulaIdUseCase,
    GetTranslatedPageUseCase,
    TranslateSectionFormulaIdUseCase,
)
from openai import AzureOpenAI, OpenAI


class AzureOcrClient:
    def __init__(self, endpoint: str, key: str, model_id: str = "prebuilt-layout"):
        """AzureOcrClientの初期化

        Args:
            endpoint (str): Azure Document Intelligenceのエンドポイント
            key (str): Azure Document Intelligenceのキー
            model_id (str): Azure Document IntelligenceのモデルID, デフォルトは"prebuilt-layout"
        """
        self._image_extractor = PyMuPDFImageExtractor()
        self._ocr_repository = AzureOCRRepository(
            endpoint=endpoint,
            key=key,
            model_id=model_id,
            image_extractor=self._image_extractor,
        )
        self._change_formula_id_usecase = ChangeFormulaIdUseCase()

    def get_document_from_path(self, document_path: str) -> Document:
        """localのファイルパスのPDFに対するAzureのOCR結果（Document）を取得する

        Args:
            document_path (str): localのファイルパス

        Returns:
            Document: AzureのOCR結果
        """
        # OCRの実行
        document, ocr_usage_stats = self._ocr_repository.get_document(document_path)

        # 数式IDの変更
        sections_with_formula_id = self._change_formula_id_usecase.execute(
            pages=document.pages,
            sections=document.sections,
        )
        document.sections = sections_with_formula_id
        document.ocr_usage_stats = ocr_usage_stats

        return document


class OpenAITranslateClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        context: str | None = None,
    ):
        """OpenAITranslateClientの初期化

        Args:
            api_key (str): OpenAIのAPIキー
            model (str): OpenAIのモデル名, e.g. "gpt-4o"
            context (str | None, optional): OpenAIのコンテキスト. Defaults to None.
        """
        self._translate_section_usecase = TranslateSectionFormulaIdUseCase(
            translate_section_repository=OpenAITranslateSectionRepository(
                client=OpenAI(api_key=api_key),
                model=model,
                context=context,
            ),
        )
        self._get_translated_page_usecase = GetTranslatedPageUseCase()

    async def translate_document(
        self,
        document: Document,
        source_language: str | None,
        target_language: str,
    ) -> TranslatedDocument:
        """OCR結果のDocumentを翻訳する

        Args:
            document (Document): OCR結果
            source_language (str | None): 翻訳元の言語(None means auto translate)
            target_language (str): 翻訳先の言語

        Returns:
            TranslatedDocument: 翻訳済みのOCR結果
        """
        # セクションごとに翻訳
        result = await self._translate_section_usecase.execute_async(
            document.sections,
            source_language=source_language,
            target_language=target_language,
        )

        # セクションごとの翻訳をページごとのデータに整形しなおす
        translated_pages = self._get_translated_page_usecase.execute(
            pages=document.pages,
            translated_sections=result.sections,
        )

        return TranslatedDocument(
            pages=translated_pages,
            sections=result.sections,
            translation_usage_stats=result.usage_stats,
        )


class AzureOpenAITranslateClient:
    def __init__(
        self,
        model: str,
        endpoint: str,
        api_key: str,
        api_version: str,
    ):
        """AzureOpenAITranslateClientの初期化

        Args:
            model (str): Azure OpenAIのモデル名, e.g. "gpt-4o"
            endpoint (str): Azure OpenAIのエンドポイント
            api_key (str): Azure OpenAIのAPIキー
            api_version (str): Azure OpenAIのAPIバージョン
        """
        self._translate_section_usecase = TranslateSectionFormulaIdUseCase(
            translate_section_repository=AzureOpenAITranslateSectionRepository(
                client=AzureOpenAI(
                    api_key=api_key,
                    azure_endpoint=endpoint,
                    api_version=api_version,
                ),
                model=model,
            ),
        )
        self._get_translated_page_usecase = GetTranslatedPageUseCase()

    async def translate_document(
        self,
        document: Document,
        source_language: str | None,
        target_language: str,
    ) -> TranslatedDocument:
        """Azure OpenAIを使用してDocumentを翻訳する

        Args:
            document (Document): OCR結果
            source_language (str | None): 翻訳元の言語(None means auto translate)
            target_language (str): 翻訳先の言語

        Returns:
            TranslatedDocument: 翻訳済みのOCR結果
        """
        # セクションごとに翻訳
        result = await self._translate_section_usecase.execute_async(
            document.sections,
            source_language=source_language,
            target_language=target_language,
        )

        # セクションごとの翻訳をページごとのデータに整形しなおす
        translated_pages = self._get_translated_page_usecase.execute(
            pages=document.pages,
            translated_sections=result.sections,
        )

        return TranslatedDocument(
            pages=translated_pages,
            sections=result.sections,
            translation_usage_stats=result.usage_stats,
        )


class DeepLTranslateClient:
    def __init__(self, api_key: str, glossary_id: str | None = None):
        """DeepLTranslateClientの初期化

        Args:
            api_key (str): DeepLのAPIキー
            glossary_id (str | None, optional): DeepLのグロサリーID. Defaults to None.
        """
        self._translate_section_usecase = TranslateSectionFormulaIdUseCase(
            translate_section_repository=DeepLTranslateSectionRepository(
                api_key=api_key,
                glossary_id=glossary_id,
            ),
        )
        self._get_translated_page_usecase = GetTranslatedPageUseCase()

    async def translate_document(
        self,
        document: Document,
        source_language: str | None,
        target_language: str,
    ) -> TranslatedDocument:
        """DeepLを使用してDocumentを翻訳する

        Args:
            document (Document): OCR結果
            source_language (str | None): 翻訳元の言語(None means auto translate)
            target_language (str): 翻訳先の言語

        Returns:
            TranslatedDocument: 翻訳済みのOCR結果
        """
        # セクションごとに翻訳
        result = await self._translate_section_usecase.execute_async(
            document.sections,
            source_language=source_language,
            target_language=target_language,
        )

        # セクションごとの翻訳をページごとのデータに整形しなおす
        translated_pages = self._get_translated_page_usecase.execute(
            pages=document.pages,
            translated_sections=result.sections,
        )

        return TranslatedDocument(
            pages=translated_pages,
            sections=result.sections,
            translation_usage_stats=result.usage_stats,
        )


class GeneratePDFClient:
    def __init__(self):
        """GeneratePDFClientの初期化

        Args:
            pdf_generator_repository (PyLaTeXGeneratePDFRepository): PDF生成器
            error_pdf_generator_repository (PyMuPDFGeneratePDFRepository): エラー時のPDF生成器
        """
        self._generate_translated_pdf_usecase = (
            GenerateTranslatedPDFWithFormulaIdUseCase(
                pdf_generator_repository=PyLaTeXGeneratePDFRepository(),
                error_pdf_generator_repository=PyMuPDFGeneratePDFRepository(),
            )
        )
        self._pdf_generator_repository = PyLaTeXGeneratePDFRepository()
        self._error_pdf_generator_repository = PyMuPDFGeneratePDFRepository()

    def generate_pdf_from_document(
        self,
        document: TranslatedDocument,
        output_doc_path: str,
    ) -> tuple[str, list[str]]:
        """翻訳済みのDocumentをPDFに変換する

        Args:
            document (TranslatedDocument): 翻訳済みのDocument
            output_doc_path (str): 出力先のパス

        Returns:
            tuple[str, list[str]]: 生成したPDFのパスと、生成したPDFのパスのリスト
        """
        # PDFの生成(latexのcompile)
        # 翻訳済みのPDFの生成. pageごとのPDFも保存する
        doc_path, page_paths = self._generate_translated_pdf_usecase.execute(
            pages_with_translations=document.pages,
            output_path=output_doc_path,
            save_page_file=True,
        )

        return doc_path, page_paths

    def generate_pdf_from_page_with_translation(
        self, page_with_translation: PageWithTranslation, output_path: str
    ) -> str:
        """翻訳済みのページをPDFに変換する

        Args:
            page_with_translation (PageWithTranslation): 翻訳済みのページ
            output_path (str): 出力先のパス

        Returns:
            str: 出力先のパス
        """
        try:
            self._pdf_generator_repository.generate_pdf_with_formula_id(
                page_with_translation, output_path
            )
        except Exception as e:
            self._error_pdf_generator_repository.generate_pdf_with_translation(
                page_with_translation, output_path
            )
        return output_path
