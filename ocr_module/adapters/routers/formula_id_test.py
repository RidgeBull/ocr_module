# %%
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

from adapters.infra.azure import AzureOCRRepository
from adapters.infra.openai import OpenAITranslateSectionRepository
from adapters.infra.pylatex import PyLaTeXGeneratePDFRepository
from adapters.infra.pymupdf import PyMuPDFImageExtractor
from usecase import (
    ChangeFormulaIdUseCase,
    GenerateTranslatedPDFWithFormulaIdUseCase,
    GetTranslatedPageUseCase,
    TranslateSectionFormulaIdUseCase,
)

english_document_path = os.path.join(project_root, "pymupdf/output/output.pdf")
english_document_output_path = os.path.join(
    project_root, "pymupdf/output/output_generated"
)

theory_document_path = os.path.join(
    project_root, "pymupdf/pdf/Zhao_Point_Transformer_ICCV_2021_paper.pdf"
)
theory_document_output_path = os.path.join(
    project_root, "pymupdf/pdf/Zhao_Point_Transformer_ICCV_2021_paper_generated"
)

math_document_path = os.path.join(project_root, "pymupdf/pdf/1255631807.pdf")
math_document_output_path = os.path.join(
    project_root, "pymupdf/pdf/1255631807_generated"
)

document_path = os.path.join(
    project_root, "pymupdf/pdf/03240441_13B_東真史_考察レポート.pdf"
)
document_output_path = os.path.join(
    project_root, "pymupdf/pdf/03240441_13B_東真史_考察レポート_generated"
)

chatgpt_document_path = os.path.join(
    project_root, "pymupdf/pdf/futureinternet-15-00192.pdf"
)
chatgpt_document_output_path = os.path.join(
    project_root, "pymupdf/pdf/futureinternet-15-00192_generated"
)

# 1. OCR
# 1.1 依存解決
ocr_repository = AzureOCRRepository(image_extractor=PyMuPDFImageExtractor())
change_formula_id_usecase = ChangeFormulaIdUseCase()

# 1.2 OCR結果の取得
document = ocr_repository.get_document(document_path=document_path)

# 1.3 数式IDの変更
sections_with_formula_id = change_formula_id_usecase.execute(
    pages=document.pages,
    sections=document.sections,
)

# 2. 翻訳

# 2.1 依存解決
translate_section_usecase = TranslateSectionFormulaIdUseCase(
    translate_section_repository=OpenAITranslateSectionRepository(),
)
get_translated_page_usecase = GetTranslatedPageUseCase()
generate_translated_pdf_usecase = GenerateTranslatedPDFWithFormulaIdUseCase(
    pdf_generator_repository=PyLaTeXGeneratePDFRepository(),
)

# 2.2 セクションごとに翻訳
translated_sections = translate_section_usecase.execute(
    sections_with_formula_id,
    source_language="en",
    target_language="ja",
)

# 2.3 セクションごとの翻訳をページごとのデータに整形しなおす
translated_pages = get_translated_page_usecase.execute(
    pages=document.pages,
    translated_sections=translated_sections,
)

# 3. PDFの生成(latexのcompile)
# 3.1 翻訳済みのPDFの生成. pageごとのPDFも保存する
translated_pdf = generate_translated_pdf_usecase.execute(
    pages_with_translations=translated_pages,
    output_path=f"{chatgpt_document_output_path}_translated.pdf",
    save_page_file=True,
)

# 3.2 翻訳前のPDFの生成(debug用). pageごとのPDFも保存する
normal_pages = [page.to_page_with_translation() for page in document.pages]
normal_pdf = generate_translated_pdf_usecase.execute(
    pages_with_translations=normal_pages,
    output_path=f"{chatgpt_document_output_path}_normal.pdf",
    save_page_file=True,
)
