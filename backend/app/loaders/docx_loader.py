from langchain_community.document_loaders import Docx2txtLoader

from app.core.errors import CorruptedFileError
from app.loaders.base import BaseLoader, PageContent

class DocxLoader(BaseLoader):
    def load(self, file_path: str) -> list[PageContent]:
        try:
            docs = Docx2txtLoader(file_path).load()
        except Exception as e:
            raise CorruptedFileError() from e

        return [PageContent(page_number=None, text=d.page_content) for d in docs]