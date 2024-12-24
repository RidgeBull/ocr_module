# %%
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

from ocr.adapters.infra.pymupdf import PyMuPDFGeneratePDFRepository
from ocr.adapters.infra.azure import AzureOcrRepository
from ocr.usecase.ocr_pdf import OCRPDFUseCase

document_path = os.path.join(project_root, "pymupdf/pdf/03240441_13B_東真史_考察レポート.pdf")
output_path = os.path.join(project_root, "pymupdf/pdf/03240441_13B_東真史_考察レポート_generated.pdf")

ocr_pdf_usecase = OCRPDFUseCase(
    ocr_repository=AzureOcrRepository(),
    pdf_repository=PyMuPDFGeneratePDFRepository(),
)
ocr_pdf_usecase.execute(document_path, output_path)
# %%
