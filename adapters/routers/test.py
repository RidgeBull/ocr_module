# %%
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

from ocr.adapters.infra.pymupdf import PyMuPDFGeneratePDFRepository
from ocr.adapters.infra.azure import AzureOcrRepository
from ocr.adapters.infra.fpdf2 import FPDF2GeneratePDFRepository
from ocr.adapters.infra.pylatex import PyLaTeXGeneratePDFRepository
from ocr.usecase.ocr_pdf import OCRPDFUseCase

english_document_path = os.path.join(project_root, "pymupdf/output/output.pdf")
english_document_output_path = os.path.join(project_root, "pymupdf/output/output_generated")

theory_document_path = os.path.join(project_root, "pymupdf/pdf/Zhao_Point_Transformer_ICCV_2021_paper.pdf")
theory_document_output_path = os.path.join(project_root, "pymupdf/pdf/Zhao_Point_Transformer_ICCV_2021_paper_generated")

document_path = os.path.join(project_root, "pymupdf/pdf/03240441_13B_東真史_考察レポート.pdf")
document_output_path = os.path.join(project_root, "pymupdf/pdf/03240441_13B_東真史_考察レポート_generated")

ocr_pdf_usecase = OCRPDFUseCase(
    ocr_repository=AzureOcrRepository(),
    pdf_repository=PyLaTeXGeneratePDFRepository(),
)
ocr_pdf_usecase.execute(english_document_path, english_document_output_path)
# %%
