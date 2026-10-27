from app.core.errors import CorruptedFileError
from app.loaders.base import BaseLoader, PageContent


class TxtLoader(BaseLoader):
    def load(self, file_path:str) -> list[PageContent]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    text = f.read()
            except Exception as e:
                raise CorruptedFileError() from e
        except OSError as e:
            raise CorruptedFileError() from e
        return [PageContent(page_number=None, text=text)]              
