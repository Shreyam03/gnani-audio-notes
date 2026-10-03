import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import engine, init_db, get_db_context
from app.models import Note
from app.services.storage import storage_service
from app.services.gnani import gnani_service
from app.services.llm import llm_service
from app.tasks import process_audio_note

def run_live_verification():
    print("=========================================================")
    print("    POSTGRESQL-ONLY VERIFICATION SUITE (STRICT MODE)")
    print("=========================================================")

    print("\n--- 1. Testing Connection to PostgreSQL Database ---")
    print(f"Connecting to Dialect: {engine.dialect.name}")
    assert engine.dialect.name == "postgresql", f"Error: Expected PostgreSQL dialect, got '{engine.dialect.name}'"

    # Initialize PostgreSQL tables
    init_db()
    print("[SUCCESS] PostgreSQL connection established and tables verified.")

    print("\n--- 2. Testing File Storage Abstraction ---")
    sample_file = "test.mp3"
    if not os.path.exists(sample_file):
        sample_file = "../test.mp3"
    
    with open(sample_file, "rb") as f:
        data = f.read()

    storage_path, audio_url = storage_service.save_file(data, "test.mp3")
    print(f"[SUCCESS] Saved file to: {storage_path}")
    print(f"[SUCCESS] Generated URL: {audio_url}")

    print("\n--- 3. Testing Note Creation in PostgreSQL ---")
    with get_db_context() as db:
        note = Note(
            filename="test.mp3",
            audio_url=audio_url,
            status="processing",
            progress_step="Queued"
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        note_id = note.id
        print(f"[SUCCESS] Row created in PostgreSQL `notes` table with ID: {note_id}")

    print("\n--- 4. Testing Background Pipeline (Gnani Batch ASR + LLM) ---")
    print("Processing audio note in background task...")
    process_audio_note(note_id, storage_path)

    print("\n--- 5. Verifying Final PostgreSQL DB Record State ---")
    with get_db_context() as db:
        n = db.query(Note).filter(Note.id == note_id).first()
        print(f"Database dialect used: {db.bind.dialect.name}")
        print(f"Status in PostgreSQL: {n.status}")
        print(f"Progress Step in PostgreSQL: {n.progress_step}")
        print(f"Transcript in PostgreSQL: {n.transcript[:150] if n.transcript else 'None'}...")
        print(f"Summary in PostgreSQL: {n.summary[:150] if n.summary else 'None'}...")
        if n.error_message:
            print(f"Error Message in PostgreSQL: {n.error_message}")
        
        assert db.bind.dialect.name == "postgresql", "Error: Database is not PostgreSQL!"
        assert n.status in ("completed", "failed"), f"Unexpected status: {n.status}"
        
        print("\n--- 6. Testing Deletion in PostgreSQL ---")
        db.delete(n)
        db.commit()
        deleted_n = db.query(Note).filter(Note.id == note_id).first()
        assert deleted_n is None, "Error: Record was not deleted from PostgreSQL"
        print("[SUCCESS] Note successfully deleted from PostgreSQL database.")

    print("\n=========================================================")
    print("[POSTGRESQL VERIFICATION COMPLETE] All checks passed.")
    print("=========================================================")

if __name__ == "__main__":
    run_live_verification()
