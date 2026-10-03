"use client";

import { useState } from "react";
import { FileText, Sparkles } from "lucide-react";
import { Note } from "@/lib/api";

interface Props {
  note: Note;
}

export default function NoteViewer({ note }: Props) {
  const [tab, setTab] = useState<"transcript" | "summary">("summary");

  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      {/* Filename header */}
      <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
        <p className="text-sm font-medium text-gray-700 truncate">{note.filename}</p>
        <p className="text-xs text-gray-400">{new Date(note.created_at).toLocaleString()}</p>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-gray-100">
        {(["summary", "transcript"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-5 py-2.5 text-sm font-medium transition-colors ${
              tab === t
                ? "border-b-2 border-blue-500 text-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t === "summary" ? (
              <Sparkles className="w-4 h-4" />
            ) : (
              <FileText className="w-4 h-4" />
            )}
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-5 max-h-96 overflow-y-auto">
        {tab === "summary" ? (
          note.summary ? (
            <div className="prose prose-sm max-w-none whitespace-pre-wrap text-gray-800 text-sm leading-relaxed">
              {note.summary}
            </div>
          ) : (
            <p className="text-sm text-gray-400 italic">No summary available.</p>
          )
        ) : (
          note.transcript ? (
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
              {note.transcript}
            </p>
          ) : (
            <p className="text-sm text-gray-400 italic">No transcript available.</p>
          )
        )}
      </div>
    </div>
  );
}
