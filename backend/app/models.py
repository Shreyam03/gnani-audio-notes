import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime
from app.db import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    filename = Column(String(255), nullable=False)

    # Permanent identifier for the file in object storage.
    # Example: audio/8f3a2c....mp3
    storage_key = Column(String(512), nullable=True)

    # Kept for frontend compatibility.
    # For private Supabase storage this will be a temporary signed URL,
    # generated/refreshed by the API rather than treated as permanent storage.
    audio_url = Column(String(1024), nullable=True)

    # State management:
    # 'processing' | 'completed' | 'failed'
    status = Column(
        String(50),
        nullable=False,
        default="processing"
    )

    # User-visible processing stage.
    progress_step = Column(
        String(255),
        nullable=False,
        default="Queued"
    )

    # Outputs
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "storage_key": self.storage_key,
            "audio_url": self.audio_url,
            "status": self.status,
            "progress_step": self.progress_step,
            "transcript": self.transcript,
            "summary": self.summary,
            "error_message": self.error_message,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
        }