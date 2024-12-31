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
    GenerateTranslatedPdfUseCase,
    GetSectionUseCase,
    GetTranslatedPageUseCase,
    OCRPDFUseCase,
    TranslateSectionUseCase,
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

ocr_pdf_usecase = OCRPDFUseCase(
    ocr_repository=AzureOCRRepository(image_extractor=PyMuPDFImageExtractor()),
    pdf_repository=PyLaTeXGeneratePDFRepository(),
)

pages = ocr_pdf_usecase.execute(
    math_document_path,
    math_document_output_path,
)

get_section_usecase = GetSectionUseCase(
    ocr_repository=AzureOCRRepository(image_extractor=PyMuPDFImageExtractor()),
)

sections = get_section_usecase.execute(
    math_document_path,
)

translate_section_usecase = TranslateSectionUseCase(
    translate_section_repository=OpenAITranslateSectionRepository(),
)

translated_sections = translate_section_usecase.execute(
    sections,
    source_language="en",
    target_language="ja",
)

get_translated_page_usecase = GetTranslatedPageUseCase()

translated_pages = get_translated_page_usecase.execute(
    pages,
    translated_sections,
)

generate_translated_pdf_usecase = GenerateTranslatedPdfUseCase(
    pdf_generator_repository=PyLaTeXGeneratePDFRepository(),
)

translated_pdf = generate_translated_pdf_usecase.execute(
    translated_pages,
    output_path=f"{math_document_output_path}_translated",
)

import re

# %%
from pylatex.utils import escape_latex

test_text = """
1808年、既知の <<formula_20>> の値に経験式を当てはめる試みの結果、ルジャンドルは以下の(2.19)で示されるものと非常によく似た近似式を予想しました。1849年、ガウスはさまざまな区間における素数の数を数えた結果に基づいて、エンケに <<formula_21>> の予想を伝えました。その予想では、数 <<formula_22>> の近傍での素数の平均密度は <<formula_23>> であるというものです。この基礎に基づき、もしすべての素数 <<formula_25>> にわたる <<formula_24>> の総和を見積もりたい場合、自然な近似式は次のようになります。
"""

formula_pattern = re.compile(r"<<formula\\_(\d+)>>")
escaped_test_text = escape_latex(test_text)
print(escaped_test_text)
formula_ids = formula_pattern.findall(escaped_test_text)
print(formula_ids)

formula_dict = {
    "20": "20",
    "21": "21",
    "22": "22",
    "23": "23",
    "25": "25",
    "24": "24",
}

for formula_id in formula_ids:
    if formula_id in formula_dict:
        escaped_test_text = escaped_test_text.replace(
            rf"<<formula\_{formula_id}>>", f"${formula_dict[formula_id]}$", 1
        )

print(escaped_test_text)

# %%
