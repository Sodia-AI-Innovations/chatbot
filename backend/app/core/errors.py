class AppError(Exception):
    status_code = 500
    message ="Something went wrong."

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)

class UnsupportedFileError(AppError):
    status_code = 415
    message = "Unsupported file type."    

class FileTooLargeError(AppError):
    status_code = 413
    message = "file is to large."

class EmptyDocumentError(AppError):
    status_code = 422
    message = "The document is empty or has no readble text."

class CorruptedFileError(AppError):
    status_code = 422
    message = "The file is corrupted or cannot be read."

class EmbeddingError(AppError):
    status_code = 502
    message = "Failed to generate embeddings."    

class VectorStoreError(AppError):
    status_code = 503
    message = "The vector databse is unavailable."    

class InvalidQuestionError(AppError):
    status_code = 422
    message = "The question is empty or too long."


class LLMError(AppError):
    status_code = 502
    message = "The language model request failed."
class DocumentNotFoundError(AppError):
    status_code = 404
    message = "Document not found."

class DatabaseError(AppError):
    status_code = 503
    message = "The database is unavailable"    


class InvalidTokenError(AppError):
    status_code = 401 
    message = "Invalid or inactive token."

class DomainNotAllowedError(AppError):
    status_code = 403
    message = "This domain is not allowed to use this chatbot."     

class InvalidDomainError(AppError):
    status_code = 422
    message = "please enter a valid website domain, eg . example.com. "   

class SiteNotFoundError(AppError):
    status_code = 404
    message = "Site not found."       

