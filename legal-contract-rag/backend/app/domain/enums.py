import enum

class ContractStatus(str, enum.Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    EXPIRED = "Expired"
    TERMINATED = "Terminated"
    ARCHIVED = "Archived"

class DocumentStatus(str, enum.Enum):
    UPLOADED = "Uploaded"
    QUEUED = "Queued"
    PROCESSING = "Processing"
    EXTRACTING_TEXT = "ExtractingText"
    CHUNKING = "Chunking"
    GENERATING_EMBEDDINGS = "GeneratingEmbeddings"
    INDEXING = "Indexing"
    COMPLETED = "Completed"
    FAILED = "Failed"

class JobOperation(str, enum.Enum):
    PROCESS = "PROCESS"
    REPROCESS = "REPROCESS"
    DELETE_INDEX = "DELETE_INDEX"

class JobStatus(str, enum.Enum):
    QUEUED = "Queued"
    IN_PROGRESS = "In_Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
