// All communication with the FastAPI backend goes through this module.

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Note {
  id: string;
  filename: string;
  audio_url: string;
  status: "processing" | "completed" | "failed";
  progress_step: string;
  transcript: string | null;
  summary: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

/** Upload an audio file. */
export async function uploadNote(file: File): Promise<Note> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE_URL}/api/notes/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail ?? `Upload failed (${res.status})`);
  }

  return res.json();
}

/** Fetch a single note and its current processing state. */
export async function getNote(id: string): Promise<Note> {
  const res = await fetch(`${API_BASE_URL}/api/notes/${id}`);

  if (!res.ok) {
    throw new Error(`Failed to fetch note ${id}`);
  }

  return res.json();
}

/** Retrieve all past notes, newest first. */
export async function listNotes(): Promise<Note[]> {
  const res = await fetch(`${API_BASE_URL}/api/notes`);

  if (!res.ok) {
    throw new Error(`Failed to fetch notes list (${res.status})`);
  }

  return res.json();
}

/** Delete a note by ID. */
export async function deleteNote(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/notes/${id}`, {
    method: "DELETE",
  });

  if (!res.ok && res.status !== 204) {
    throw new Error(`Failed to delete note ${id} (${res.status})`);
  }
}