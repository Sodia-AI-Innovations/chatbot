
from abc import ABC, abstractmethod
from dataclasses import dataclass
@dataclass
class PageContent:
    page_number: int | None
    text: str

class BaseLoader(ABC):
    @abstractmethod
    def load(self, file_path: str) -> list[PageContent]:
        """Read a file and return its text as a list of pages."""  