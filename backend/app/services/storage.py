import mimetypes
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import settings

from supabase import Client, create_client


class BaseStorageService(ABC):
    """Common interface for local and cloud object storage."""

    @abstractmethod
    def save_file(
        self,
        file_content: bytes,
        original_filename: str,
    ) -> tuple[str, str]:
        """
        Save a file.

        Returns:
            (storage_key_or_path, accessible_url)
        """
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Delete a stored file."""
        raise NotImplementedError

    @abstractmethod
    def get_access_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
    ) -> str:
        """Return a URL through which the stored file can be accessed."""
        raise NotImplementedError


class LocalStorageService(BaseStorageService):
    """Local filesystem storage used during development."""

    def __init__(
        self,
        upload_dir: Path = settings.STORAGE_DIR,
        base_url: str = settings.BASE_URL,
    ):
        self.upload_dir = upload_dir
        self.base_url = base_url

        self.upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save_file(
        self,
        file_content: bytes,
        original_filename: str,
    ) -> tuple[str, str]:

        extension = Path(original_filename).suffix or ".mp3"
        safe_filename = f"{uuid.uuid4().hex}{extension}"

        target_path = self.upload_dir / safe_filename

        with open(target_path, "wb") as f:
            f.write(file_content)

        audio_url = (
            f"{self.base_url}/media/{safe_filename}"
        )

        return str(target_path), audio_url

    def delete_file(self, storage_path: str) -> bool:
        try:
            if os.path.exists(storage_path):
                os.remove(storage_path)
                return True
        except OSError:
            pass

        return False

    def get_access_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
    ) -> str:
        """
        For local development, the media URL does not expire.
        """
        filename = Path(storage_path).name

        return f"{self.base_url}/media/{filename}"


class SupabaseStorageService(BaseStorageService):
    """
    Supabase Storage implementation for deployed environments.

    The bucket is private, so browser access uses a temporary
    signed URL rather than a permanent public URL.
    """

    def __init__(
        self,
        supabase_url: str = settings.SUPABASE_URL,
        secret_key: str = settings.SUPABASE_SECRET_KEY,
        bucket: str = settings.SUPABASE_BUCKET,
    ):
        if not supabase_url:
            raise ValueError(
                "SUPABASE_URL is not configured"
            )

        if not secret_key:
            raise ValueError(
                "SUPABASE_SECRET_KEY is not configured"
            )

        if not bucket:
            raise ValueError(
                "SUPABASE_BUCKET is not configured"
            )

        self.bucket = bucket

        self.client: Client = create_client(
            supabase_url,
            secret_key,
        )

    def save_file(
        self,
        file_content: bytes,
        original_filename: str,
    ) -> tuple[str, str]:

        extension = (
            Path(original_filename).suffix.lower()
            or ".mp3"
        )

        storage_key = (
            f"audio/{uuid.uuid4().hex}{extension}"
        )

        content_type = (
            mimetypes.guess_type(original_filename)[0]
            or "application/octet-stream"
        )

        self.client.storage.from_(self.bucket).upload(
            path=storage_key,
            file=file_content,
            file_options={
                "content-type": content_type,
                "upsert": "false",
            },
        )

        # Generate a temporary browser-accessible URL.
        audio_url = self.get_access_url(
            storage_key,
            expires_in=3600,
        )

        return storage_key, audio_url

    def delete_file(self, storage_path: str) -> bool:
        try:
            self.client.storage.from_(self.bucket).remove(
                [storage_path]
            )
            return True
        except Exception:
            return False

    def get_access_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
    ) -> str:

        response = (
            self.client.storage
            .from_(self.bucket)
            .create_signed_url(
                storage_path,
                expires_in,
            )
        )

        signed_url = (
            response.get("signedUrl")
            or response.get("signedURL")
        )

        if not signed_url:
            raise RuntimeError(
                f"Supabase did not return a signed URL "
                f"for {storage_path}"
            )

        return signed_url


def _create_storage_service() -> BaseStorageService:
    """
    Use Supabase when cloud credentials are configured.
    Otherwise use local storage for development.
    """

    if (
        settings.SUPABASE_URL
        and settings.SUPABASE_SECRET_KEY
    ):
        return SupabaseStorageService()

    return LocalStorageService()


storage_service = _create_storage_service()