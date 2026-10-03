import os
import time
import json
import requests
from app.config import settings

TERMINAL_STATES = {"COMPLETED", "PARTIAL_FAILURE", "FAILED", "START_FAILED", "CANCELLED"}

class GnaniASRService:
    def __init__(self, api_key: str = settings.GNANI_API_KEY, base_url: str = settings.GNANI_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key-ID": self.api_key}

    def transcribe_audio(self, file_path: str, progress_callback=None) -> str:
        """
        Executes full batch STT pipeline:
        1. Create job
        2. Start job
        3. Poll job (respecting API guidelines)
        4. Fetch & return formatted transcript
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found at path: {file_path}")

        if not self.api_key:
            raise ValueError("GNANI_API_KEY is not configured in backend environment")

        # Step 1: Create Job
        if progress_callback:
            progress_callback("Submitting audio to Gnani ASR Batch API")
        job_id = self._create_job(file_path)

        # Step 2: Start Job
        if progress_callback:
            progress_callback("Starting Gnani ASR batch transcription")
        self._start_job(job_id)

        # Step 3: Poll Job Status (5s initial delay, 5s interval polling loop)
        if progress_callback:
            progress_callback("Transcribing audio (Gnani ASR processing)")
        final_job = self._poll_job_status(job_id)

        if final_job.get("status") != "COMPLETED":
            error_reason = final_job.get("error_message") or final_job.get("status") or "Unknown ASR Error"
            raise RuntimeError(f"Gnani ASR transcription failed: {error_reason}")

        # Step 4: Fetch Transcript Results
        if progress_callback:
            progress_callback("Downloading transcript results")
        return self._fetch_transcript(job_id)

    def transcribe_from_url(self, audio_url: str, progress_callback=None) -> str:
        """
        Transcribe an audio file available at an HTTPS URL using
        Gnani Batch cloud-storage input.
        """

        if not audio_url:
            raise ValueError("Audio URL is required")

        if not self.api_key:
            raise ValueError("GNANI_API_KEY is not configured")

        if progress_callback:
            progress_callback("Submitting audio to Gnani ASR Batch API")

        job_id = self._create_job_from_url(audio_url)

        if progress_callback:
            progress_callback("Starting Gnani ASR batch transcription")

        self._start_job(job_id)

        if progress_callback:
            progress_callback("Transcribing audio (Gnani ASR processing)")

        final_job = self._poll_job_status(job_id)

        if final_job.get("status") != "COMPLETED":
            error_reason = (
                final_job.get("error_message")
                or final_job.get("status")
                or "Unknown ASR Error"
            )
            raise RuntimeError(
                f"Gnani ASR transcription failed: {error_reason}"
            )

        if progress_callback:
            progress_callback("Downloading transcript results")

        return self._fetch_transcript(job_id)

    def _create_job(self, file_path: str) -> str:
        config = {
            "model": "gnani-prisma-v2.5",
            "language_code": "en-IN",
            "mode": "transcribe"
        }

        with open(file_path, "rb") as f:
            audio_data = f.read()

        response = requests.post(
            f"{self.base_url}/stt/v3/batch/jobs",
            headers=self.headers,
            files={
                "config": (None, json.dumps(config), "application/json"),
                "files": (os.path.basename(file_path), audio_data, "audio/mpeg"),
            },
            timeout=90,
        )

        if response.status_code != 200 and response.status_code != 201:
            raise RuntimeError(f"Failed to create Gnani ASR job (HTTP {response.status_code}): {response.text}")

        res_json = response.json()
        job_id = res_json.get("job_id")
        if not job_id:
            raise RuntimeError(f"Invalid response from Gnani API: {response.text}")
        return job_id
    def _create_job_from_url(self, audio_url: str) -> str:
        config = {
            "model": "gnani-prisma-v2.5",
            "language_code": "en-IN",
            "mode": "transcribe",
            "with_diarization": False,
            "is_multi_channel": False,
            "with_denoise": False,
        }

        payload = {
            "config": config,
            "source": {
                "type": "cloud_storage",
                "auth": {
                    "mode": "public"
                },
                "paths": [audio_url],
            },
        }

        response = requests.post(
            f"{self.base_url}/stt/v3/batch/jobs",
            headers={
                **self.headers,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Failed to create Gnani ASR job "
                f"(HTTP {response.status_code}): {response.text}"
            )

        data = response.json()
        job_id = data.get("job_id")

        if not job_id:
            raise RuntimeError(
                f"Invalid response from Gnani API: {response.text}"
            )

        return job_id
    
    def _start_job(self, job_id: str, max_retries: int = 4):
        """
        Start a Gnani batch job.
        Retries rate-limit (429) responses with exponential backoff.
        """
        for attempt in range(max_retries + 1):
            response = requests.post(
                f"{self.base_url}/stt/v3/batch/jobs/{job_id}/start",
                headers=self.headers,
                timeout=30,
            )

            if response.status_code in (200, 201, 202):
                return

            if response.status_code == 429 and attempt < max_retries:
                wait_seconds = 10 * (2 ** attempt)
                print(
                    f"Gnani rate limit hit while starting job {job_id}. "
                    f"Retrying in {wait_seconds}s..."
                )
                time.sleep(wait_seconds)
                continue

            raise RuntimeError(
                f"Failed to start Gnani ASR job {job_id} "
                f"(HTTP {response.status_code}): {response.text}"
            )

    def _poll_job_status(self, job_id: str, max_attempts: int = 60, poll_interval: int = 10) -> dict:
        """
        Polls job status respecting official Gnani API guidance:
        - 10-second initial delay after start
        - 10-second polling interval
        """
        time.sleep(10)  # Initial delay recommended by official API docs

        for _ in range(max_attempts):
            response = requests.get(
                f"{self.base_url}/stt/v3/batch/jobs/{job_id}",
                headers=self.headers,
                timeout=30,
            )
            if response.status_code == 200:
                job_data = response.json()
                status = job_data.get("status")
                if status in TERMINAL_STATES:
                    return job_data

            time.sleep(poll_interval)

        raise TimeoutError(f"Gnani ASR job {job_id} timed out after {max_attempts * poll_interval} seconds")

    def _fetch_transcript(self, job_id: str, max_retries: int = 4) -> str:
        """
        Fetch completed transcript files and download their transcript JSON.
        Retries temporary 429 rate-limit responses with exponential backoff.
        """
        for attempt in range(max_retries + 1):
            response = requests.get(
                f"{self.base_url}/stt/v3/batch/jobs/{job_id}/files?status=COMPLETED",
                headers=self.headers,
                timeout=30,
            )

            if response.status_code == 200:
                response_data = response.json()

                files = response_data.get("data", [])

                if not files:
                    raise RuntimeError(
                        f"No completed transcript files found for Gnani job {job_id}"
                    )

                transcripts = []

                for file_info in files:
                    transcript_url = file_info.get("transcript_url")

                    if not transcript_url:
                        continue

                    # Presigned URL: do NOT send the Gnani API key here.
                    transcript_response = requests.get(
                        transcript_url,
                        timeout=30,
                    )

                    if transcript_response.status_code != 200:
                        raise RuntimeError(
                            f"Failed to download transcript for job {job_id}: "
                            f"HTTP {transcript_response.status_code}"
                        )

                    transcript_data = transcript_response.json()
                    full_transcript = transcript_data.get(
                        "full_transcript", ""
                    ).strip()

                    if full_transcript:
                        transcripts.append(full_transcript)

                if not transcripts:
                    raise RuntimeError(
                        f"Gnani returned completed files but no transcript text "
                        f"for job {job_id}"
                    )

                return "\n\n".join(transcripts)

            if response.status_code == 429 and attempt < max_retries:
                wait_seconds = 10 * (2 ** attempt)

                print(
                    f"Gnani rate limit hit while fetching transcript for "
                    f"{job_id}. Retrying in {wait_seconds}s..."
                )

                time.sleep(wait_seconds)
                continue

            raise RuntimeError(
                f"Failed to fetch transcript files for job {job_id}: "
                f"{response.text}"
            )

        raise RuntimeError(
            f"Failed to fetch transcript files for job {job_id} "
            f"after {max_retries + 1} attempts"
        )

gnani_service = GnaniASRService()
