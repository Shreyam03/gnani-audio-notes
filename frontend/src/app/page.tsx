"use client";
import Link from "next/link";
import { useEffect, useState, useCallback } from "react";
import AudioUploader from "@/components/AudioUploader";
import ProcessingStatus from "@/components/ProcessingStatus";
import NoteViewer from "@/components/NoteViewer";
import NoteHistory from "@/components/NoteHistory";
import { Note, listNotes } from "@/lib/api";

export default function Home() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [activeNote, setActiveNote] = useState<Note | null>(null);

  // Load history on mount
  useEffect(() => {
    listNotes().then(setNotes).catch(console.error);
  }, []);

  // Called immediately after upload → 202 returned
  function handleUploaded(note: Note) {
    setNotes((prev) => [note, ...prev]);
    setActiveNote(note);
  }

  // Called by ProcessingStatus whenever it polls a new state
  const handleNoteUpdate = useCallback((updated: Note) => {
    setNotes((prev) => prev.map((n) => (n.id === updated.id ? updated : n)));
    setActiveNote((prev) => (prev?.id === updated.id ? updated : prev));
  }, []);

  // Called by NoteHistory when user selects a past note
  function handleSelect(note: Note) {
    setActiveNote(note);
  }

  // Called by NoteHistory after successful deletion
  function handleDelete(id: string) {
    setNotes((prev) => prev.filter((n) => n.id !== id));
    if (activeNote?.id === id) setActiveNote(null);
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Left: Upload + Active note */}
      <div className="md:col-span-2 space-y-5">
        <div>
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-semibold text-slate-900">
              New Recording
            </h1>

            <Link
              href="/architecture"
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900"
            >
              Architecture
              <span aria-hidden="true">→</span>
            </Link>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Upload any audio file. Long recordings are transcribed using{" "}
            <span className="font-medium text-gray-700">Gnani Batch ASR</span>.
          </p>
          <AudioUploader onUploaded={handleUploaded} />
        </div>

        {/* Active note state */}
        {activeNote && (
          <div className="space-y-4">
            {activeNote.status === "processing" && (
              <ProcessingStatus note={activeNote} onUpdate={handleNoteUpdate} />
            )}
            {activeNote.status === "completed" && (
              <NoteViewer note={activeNote} />
            )}
            {activeNote.status === "failed" && (
              <div className="rounded-xl border border-red-200 bg-red-50 p-4">
                <p className="text-sm font-medium text-red-700">Processing failed</p>
                <p className="text-xs text-red-500 mt-1">{activeNote.error_message}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right: History sidebar */}
      <div className="md:col-span-1">
        <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
          Past Notes
        </h2>
        <div className="bg-white border border-gray-200 rounded-xl p-2">
          <NoteHistory
            notes={notes}
            activeId={activeNote?.id ?? null}
            onSelect={handleSelect}
            onDelete={handleDelete}
          />
        </div>
      </div>
    </div>
  );
}
