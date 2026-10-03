
from app.db import get_db_context
from app.models import Note
from app.services.gnani import gnani_service
from app.services.llm import llm_service
from app.services.storage import storage_service


def process_audio_note(note_id: str, storage_key: str):
    """
    Background worker task executed by FastAPI BackgroundTasks.

    Pipeline:
    1. Update note status/progress
    2. Generate a signed URL for the stored audio
    3. Send the URL to Gnani Batch STT
    4. Save the transcript
    5. Generate an LLM summary
    6. Save the summary and mark the note completed
    7. Store a visible error state if anything fails
    """

    with get_db_context() as db:
        note = db.query(Note).filter(Note.id == note_id).first()

        if not note:
            return

        try:
            # ---------------------------------------------------------
            # 1. Start processing
            # ---------------------------------------------------------
            note.status = "processing"
            note.progress_step = "Transcribing audio with Gnani ASR"
            db.commit()

            # ---------------------------------------------------------
            # 2. Progress callback used by Gnani service
            # ---------------------------------------------------------
            def update_progress(step_msg: str):
                try:
                    with get_db_context() as inner_db:
                        current_note = (
                            inner_db.query(Note)
                            .filter(Note.id == note_id)
                            .first()
                        )

                        if current_note:
                            current_note.progress_step = step_msg
                            inner_db.commit()

                except Exception:
                    # Progress update failure should not break
                    # the actual transcription pipeline.
                    pass

            # ---------------------------------------------------------
            # 3. Generate a fresh signed URL for the stored audio
            # ---------------------------------------------------------
            audio_access_url = storage_service.get_access_url(
                storage_key,
                expires_in=3600,
            )

            # ---------------------------------------------------------
            # 4. Run Gnani Batch STT using the signed HTTPS URL
            # ---------------------------------------------------------
            transcript = gnani_service.transcribe_from_url(
                audio_access_url,
                progress_callback=update_progress,
            )

            if not transcript or not transcript.strip():
                raise RuntimeError(
                    "Gnani returned an empty transcript."
                )

            # ---------------------------------------------------------
            # 5. Save transcript + move to summary stage
            # ---------------------------------------------------------
            with get_db_context() as inner_db:
                current_note = (
                    inner_db.query(Note)
                    .filter(Note.id == note_id)
                    .first()
                )

                if current_note:
                    current_note.transcript = transcript
                    current_note.progress_step = "Generating AI summary"
                    inner_db.commit()

            # ---------------------------------------------------------
            # 6. Generate LLM summary
            # ---------------------------------------------------------
            summary = llm_service.generate_summary(transcript)

            if not summary or not summary.strip():
                raise RuntimeError(
                    "LLM returned an empty summary."
                )

            # ---------------------------------------------------------
            # 7. Save summary + mark completed
            # ---------------------------------------------------------
            with get_db_context() as inner_db:
                current_note = (
                    inner_db.query(Note)
                    .filter(Note.id == note_id)
                    .first()
                )

                if current_note:
                    current_note.summary = summary
                    current_note.status = "completed"
                    current_note.progress_step = "Completed"
                    current_note.error_message = None
                    inner_db.commit()

        except Exception as e:
            # ---------------------------------------------------------
            # 8. Visible failure handling
            # ---------------------------------------------------------
            error_msg = str(e)

            with get_db_context() as inner_db:
                current_note = (
                    inner_db.query(Note)
                    .filter(Note.id == note_id)
                    .first()
                )

                if current_note:
                    current_note.status = "failed"
                    current_note.progress_step = (
                        f"Failed: {error_msg[:100]}"
                    )
                    current_note.error_message = error_msg
                    inner_db.commit()
