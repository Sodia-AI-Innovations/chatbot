from app.core.errors import UnsupportedFileError
from app.loaders.base import BaseLoader
from app.loaders.docx_loader import DocxLoader
from app.loaders.pdf_loader import PdfLoader
from app.loaders.txt_loader import TxtLoader

LOADERS: dict[str,type[BaseLoader]] ={
    "pdf": PdfLoader,
    "docx": DocxLoader,
    "txt": TxtLoader,
}

def get_loader(extension: str) -> BaseLoader:
    loader_cls = LOADERS.get(extension.lower())
    if loader_cls is None:
        raise UnsupportedFileError(f"No loader for '.{extension}' files.")
    return loader_cls()