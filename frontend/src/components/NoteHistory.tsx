"use client";

import { Trash2, Loader2, CheckCircle, XCircle, Clock } from "lucide-react";
import { Note, deleteNote } from "@/lib/api";

interface Props {
  notes: Note[];
  activeId: string | null;
  onSelect: (note: Note) => void;
  onDelete: (id: string) => void;
}

function StatusIcon({ status }: { status: Note["status"] }) {
  if (status === "completed") return <CheckCircle className="w-3.5 h-3.5 text-green-500" />;
  if (status === "failed") return <XCircle className="w-3.5 h-3.5 text-red-400" />;
  return <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />;
}

export default function NoteHistory({ notes, activeId, onSelect, onDelete }: Props) {
  async function handleDelete(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    try {
      await deleteNote(id);
      onDelete(id);
    } catch {
      alert("Failed to delete note.");
    }
  }

  if (notes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-10 text-gray-400">
        <Clock className="w-6 h-6" />
        <p className="text-sm">No past notes yet</p>
      </div>
    );
  }

  return (
    <ul className="space-y-1">
      {notes.map((note) => (
        <li
          key={note.id}
          onClick={() => onSelect(note)}
          className={`flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer group transition-colors ${
            activeId === note.id
              ? "bg-blue-50 border border-blue-200"
              : "hover:bg-gray-100 border border-transparent"
          }`}
        >
          <StatusIcon status={note.status} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-700 truncate">{note.filename}</p>
            <p className="text-xs text-gray-400 truncate">{note.progress_step}</p>
          </div>
          <button
            onClick={(e) => handleDelete(e, note.id)}
            className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity p-0.5 rounded"
            title="Delete note"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </li>
      ))}
    </ul>
  );
}
