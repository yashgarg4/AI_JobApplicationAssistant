from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import pypdf
import docx # python-docx
import os

class FilePathInput(BaseModel):
    file_path: str = Field(..., description="The local file path to the document (PDF or DOCX).")

class ResumeParserTool(BaseTool):
    name: str = "Resume Parser Tool"
    description: str = (
        "Parses a resume file (PDF or DOCX) provided as a file path and extracts its text content. "
        "Returns the full text content of the resume."
    )
    args_schema: type[BaseModel] = FilePathInput

    def _run(self, file_path: str) -> str:
        text = ""
        try:
            if not os.path.exists(file_path):
                return f"Error: File not found at path: {file_path}"

            if file_path.lower().endswith(".pdf"):
                with open(file_path, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() or ""
            elif file_path.lower().endswith(".docx"):
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            else:
                return "Error: Unsupported file type. Please provide a PDF or DOCX file path."
            
            if not text.strip():
                return "Error: Could not extract text from the resume. The file might be empty, scanned as an image, or corrupted."
            return text
        except Exception as e:
            return f"Error parsing resume at path {file_path}: {str(e)}"