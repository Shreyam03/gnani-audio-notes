"use client";

import { useEffect, useRef } from "react";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { getNote, Note } from "@/lib/api";

interface Props {
  note: Note;
  onUpdate: (note: Note) => void;
}

const TERMINAL = ["completed", "failed"];
const POLL_MS = 3000;

export default function ProcessingStatus({ note, onUpdate }: Props) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (TERMINAL.includes(note.status)) return;

    async function poll() {
      try {
        const updated = await getNote(note.id);
        onUpdate(updated);
        if (!TERMINAL.includes(updated.status)) {
          timerRef.current = setTimeout(poll, POLL_MS);
        }
      } catch {
        // network blip — retry
        timerRef.current = setTimeout(poll, POLL_MS);
      }
    }

    timerRef.current = setTimeout(poll, POLL_MS);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [note.id, note.status]); // eslint-disable-line react-hooks/exhaustive-deps

  const isProcessing = note.status === "processing";
  const isCompleted = note.status === "completed";
  const isFailed = note.status === "failed";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 space-y-3">
      <div className="flex items-center gap-3">
        {isProcessing && <Loader2 className="w-5 h-5 text-blue-500 animate-spin flex-shrink-0" />}
        {isCompleted && <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />}
        {isFailed && <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />}

        <div>
          <p className="text-sm font-medium text-gray-800 truncate max-w-xs">{note.filename}</p>
          <p className={`text-xs mt-0.5 ${isFailed ? "text-red-500" : "text-gray-500"}`}>
            {note.progress_step}
          </p>
        </div>
      </div>

      {/* Progress steps */}
      <div className="flex gap-2 flex-wrap">
        {[
          "Queued",
          "Transcribing audio with Gnani ASR",
          "Generating AI summary",
          "Completed",
        ].map((step) => {
          const stepIndex = [
            "Queued",
            "Transcribing audio with Gnani ASR",
            "Generating AI summary",
            "Completed",
          ].indexOf(step);

          const currentIndex = isFailed
            ? -1
            : [
                "Queued",
                "Transcribing audio with Gnani ASR",
                "Generating AI summary",
                "Completed",
              ].indexOf(note.progress_step);

          const done = isCompleted || currentIndex > stepIndex;
          const active = !isFailed && note.progress_step === step;

          return (
            <span
              key={step}
              className={`text-xs px-2 py-1 rounded-full border ${
                done || active
                  ? "bg-blue-100 border-blue-300 text-blue-700 font-medium"
                  : "bg-gray-100 border-gray-200 text-gray-400"
              }`}
            >
              {step}
            </span>
          );
        })}
      </div>

      {isFailed && note.error_message && (
        <p className="text-xs text-red-600 bg-red-50 rounded p-2 break-words">
          {note.error_message}
        </p>
      )}
    </div>
  );
}
