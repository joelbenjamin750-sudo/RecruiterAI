import os
from pypdf import PdfReader
from typing import Optional

class PDFService:
    """
    Service to handle PDF processing and text extraction from resumes.
    """

    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """
        Reads a PDF file and extracts all text content.

        Args:
            file_path (str): Absolute path to the PDF file.

        Returns:
            Optional[str]: The extracted text if successful, None otherwise.
        """
        try:
            if not os.path.exists(file_path):
                print(f"Error: File not found at {file_path}")
                return None

            reader = PdfReader(file_path)
            text = ""

            # Extract text from each page
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            # Clean up extra whitespace and empty lines
            cleaned_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])

            return cleaned_text if cleaned_text else None

        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None

    @staticmethod
    def save_upload(file_content: bytes, filename: str, upload_dir: str = "uploads") -> Optional[str]:
        """
        Saves uploaded file bytes to a local directory.

        Args:
            file_content (bytes): The raw bytes of the uploaded file.
            filename (str): The name of the file.
            upload_dir (str): Directory where files should be stored.

        Returns:
            Optional[str]: The absolute path to the saved file, or None if failed.
        """
        try:
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            file_path = os.path.join(upload_dir, filename)

            with open(file_path, "wb") as f:
                f.write(file_content)

            return os.path.abspath(file_path)
        except Exception as e:
            print(f"Error saving upload: {e}")
            return None
