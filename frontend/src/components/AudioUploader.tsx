"use client";

import { useRef, useState, DragEvent, ChangeEvent } from "react";
import { UploadCloud } from "lucide-react";
import { uploadNote, Note } from "@/lib/api";

interface Props {
  onUploaded: (note: Note) => void;
}

const ACCEPTED = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"];

export default function AudioUploader({ onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setError(null);
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setError(`Unsupported format "${ext}". Allowed: ${ACCEPTED.join(", ")}`);
      return;
    }
    try {
      setUploading(true);
      // POST /api/notes/upload → 202 Accepted + Note JSON immediately
      const note = await uploadNote(file);
      onUploaded(note);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function onChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    // reset so the same file can be re-selected
    e.target.value = "";
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-xl p-10 flex flex-col items-center gap-3
          cursor-pointer transition-colors select-none
          ${dragging ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50"}
          ${uploading ? "opacity-60 cursor-not-allowed" : ""}
        `}
      >
        <UploadCloud className="w-10 h-10 text-blue-500" />
        {uploading ? (
          <p className="text-sm text-gray-500">Uploading…</p>
        ) : (
          <>
            <p className="text-sm font-medium text-gray-700">
              Drag &amp; drop an audio file, or click to browse
            </p>
            <p className="text-xs text-gray-400">{ACCEPTED.join("  ·  ")}</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(",")}
          className="hidden"
          onChange={onChange}
          disabled={uploading}
        />
      </div>

      {error && (
        <p className="mt-2 text-sm text-red-600 bg-red-50 rounded p-2">{error}</p>
      )}
    </div>
  );
}
