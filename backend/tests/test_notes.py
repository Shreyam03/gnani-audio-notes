import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.db import init_db, engine, SessionLocal
from app.models import Note

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def setup_postgres_db():
    """Ensure PostgreSQL database tables exist before running test suite"""
    init_db()
    yield

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_upload_audio_returns_202_accepted():
    fake_audio = b"ID3\x03\x00\x00\x00\x00\x00\x00Fake MP3 Audio Content Header"
    
    response = client.post(
        "/api/notes/upload",
        files={"file": ("test_sample.mp3", fake_audio, "audio/mpeg")}
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["filename"] == "test_sample.mp3"
    assert data["status"] == "processing"
    assert data["progress_step"] == "Queued"
    assert data["audio_url"].endswith(".mp3")

def test_list_and_get_note():
    fake_audio = b"ID3\x03\x00\x00\x00\x00\x00\x00Fake Audio Data"
    
    upload_res = client.post(
        "/api/notes/upload",
        files={"file": ("sample2.mp3", fake_audio, "audio/mpeg")}
    )
    note_id = upload_res.json()["id"]

    # List notes from PostgreSQL
    list_res = client.get("/api/notes")
    assert list_res.status_code == 200
    notes = list_res.json()
    assert len(notes) >= 1
    assert any(n["id"] == note_id for n in notes)

    # Get single note from PostgreSQL
    get_res = client.get(f"/api/notes/{note_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == note_id

def test_delete_note():
    fake_audio = b"ID3\x03\x00\x00\x00\x00\x00\x00Fake Audio Data"
    upload_res = client.post(
        "/api/notes/upload",
        files={"file": ("delete_me.mp3", fake_audio, "audio/mpeg")}
    )
    note_id = upload_res.json()["id"]

    # Delete note from PostgreSQL
    del_res = client.delete(f"/api/notes/{note_id}")
    assert del_res.status_code == 204

    # Verify 404 on get from PostgreSQL
    get_res = client.get(f"/api/notes/{note_id}")
    assert get_res.status_code == 404

def test_invalid_extension_failure_handling():
    invalid_file = b"Not an audio file"
    response = client.post(
        "/api/notes/upload",
        files={"file": ("virus.exe", invalid_file, "application/x-msdownload")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]
