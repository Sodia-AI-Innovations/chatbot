from langchain_community.document_loaders import PyPDFLoader

from app.core.errors import CorruptedFileError
from app.loaders.base import BaseLoader, PageContent

class PdfLoader(BaseLoader):
    def load(self, file_path: str) -> list[PageContent]:
        try:
            docs = PyPDFLoader(file_path).load()
        except Exception as e:
            raise CorruptedFileError() from e

        return [
            PageContent(page_number=d.metadata.get("page",i) + 1, text=d.page_content)
            for i,d in enumerate(docs)
        ]    

