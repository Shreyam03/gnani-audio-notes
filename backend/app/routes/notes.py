from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import Note
from app.services.storage import storage_service
from app.tasks import process_audio_note

router = APIRouter(prefix="/api/notes", tags=["notes"])

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_audio_note(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts audio file upload of any size/length.
    Saves file to storage, creates Note in DB, enqueues background processing task.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")

    filename = file.filename
    ext = filename.lower()[filename.rfind("."):] if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read binary content
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Save to storage service abstraction
    
    storage_key, audio_url = storage_service.save_file(content, filename)

    # Create Note DB record
    note = Note(
        filename=filename,
        storage_key=storage_key,
        audio_url=audio_url,
        status="processing",
        progress_step="Queued"
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    # Enqueue FastAPI background task
    background_tasks.add_task(
    process_audio_note,
    note.id,
    storage_key
    )

    return note.to_dict()


@router.get("", response_model=List[dict])
def list_notes(db: Session = Depends(get_db)):
    """Returns list of past notes ordered by creation time descending"""
    notes = db.query(Note).order_by(Note.created_at.desc()).all()
    return [note.to_dict() for note in notes]


@router.get("/{note_id}")
def get_note(note_id: str, db: Session = Depends(get_db)):
    """Returns single note details including processing status, transcript, and summary"""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Audio note not found")
    return note.to_dict()


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: str, db: Session = Depends(get_db)):
    """Deletes note record and associated audio file"""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Audio note not found")

    # Clean up audio file
    if note.storage_key:
        storage_service.delete_file(note.storage_key)
    db.delete(note)
    db.commit()
    return None
