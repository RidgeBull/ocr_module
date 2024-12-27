# %%
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

from ocr.adapters.infra.pymupdf import (
    PyMuPDFGeneratePDFRepository,
    PyMuPDFImageExtractor,
)
from ocr.adapters.infra.azure import AzureOcrRepository
from ocr.adapters.infra.fpdf2 import FPDF2GeneratePDFRepository
from ocr.adapters.infra.pylatex import PyLaTeXGeneratePDFRepository
from ocr.adapters.infra.openai import OpenAITranslateSectionRepository
from ocr.usecase import OCRPDFUseCase, TranslatePDFUseCase

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

document_path = os.path.join(
    project_root, "pymupdf/pdf/03240441_13B_東真史_考察レポート.pdf"
)
document_output_path = os.path.join(
    project_root, "pymupdf/pdf/03240441_13B_東真史_考察レポート_generated"
)

ocr_pdf_usecase = OCRPDFUseCase(
    ocr_repository=AzureOcrRepository(image_extractor=PyMuPDFImageExtractor()),
    pdf_repository=PyLaTeXGeneratePDFRepository(),
)

translate_pdf_usecase = TranslatePDFUseCase(
    translate_section_repository=OpenAITranslateSectionRepository(),
    pdf_generator_repository=PyLaTeXGeneratePDFRepository(),
    ocr_repository=AzureOcrRepository(image_extractor=PyMuPDFImageExtractor()),
)

translate_pdf_usecase.execute(
    theory_document_path,
    theory_document_output_path,
    "en",
    "ja",
)
# %%
