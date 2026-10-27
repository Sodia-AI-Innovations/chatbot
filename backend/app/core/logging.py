import logging
import sys
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True

 
def setup_logging(level: str = "INFO") -> None:
    logging.getLogger("google_genai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(request_id)s | %(name)s | %(message)s"
    ))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)