import os
from app.core.config import get_settings
from app.core.errors import EmptyDocumentError, FileTooLargeError, UnsupportedFileError

def validate_file(filename: str, size_bytes: int)-> str:
    """ check extension and size. Return the lowercase extension."""

    settings = get_settings()

    extension = os.path.splitext(filename)[1].lstrip(".").lower()
    if extension not in settings.allowed_ext_list:
        raise UnsupportedFileError(
            f"'.{extension}' is not supported. Allowed: {','.join(settings.allowed_ext_list)}"
        )

    if size_bytes == 0:
        raise EmptyDocumentError("The uploaded file is empty.")

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileTooLargeError(f"File Exceeds {settings.max_file_size_mb} MB limit.")
    return extension