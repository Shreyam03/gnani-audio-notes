
import Link from "next/link";
export default function ArchitecturePage() {
  return (
    <main className="min-h-screen bg-white text-slate-900">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="mb-10">
          <Link
            href="/"
            className="text-sm font-medium text-slate-500 hover:text-slate-900"
          >
            ← Back to notes
          </Link>

          <h1 className="mt-6 text-4xl font-bold tracking-tight">
            Architecture
          </h1>
          <p className="mt-3 max-w-3xl text-lg text-slate-600">
            How the Audio Notes platform handles uploads, transcription,
            summaries, storage, background processing, and failures.
          </p>
        </div>

        <section className="mb-10">
          <h2 className="text-2xl font-semibold">System flow</h2>

          <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-6">
            <div className="flex flex-wrap items-center justify-center gap-3 text-sm font-medium">
              {[
                "Next.js",
                "FastAPI",
                "Supabase Storage",
                "Background Task",
                "Gnani Batch ASR",
                "PostgreSQL",
                "Gemini",
              ].map((item, index, items) => (
                <div key={item} className="flex items-center gap-3">
                  <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm">
                    {item}
                  </div>
                  {index < items.length - 1 && (
                    <span className="text-slate-400">→</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          <p className="mt-5 leading-7 text-slate-600">
            A user uploads an audio file from the Next.js frontend. FastAPI
            stores the file in Supabase Storage and creates a note record in
            PostgreSQL. The API immediately returns the note ID and the
            frontend can show that processing has started.
          </p>

          <p className="mt-4 leading-7 text-slate-600">
            The actual transcription and summarization happen in a background
            task. The task obtains a temporary signed URL for the stored audio,
            sends that URL to Gnani's Batch ASR API, polls for completion,
            retrieves the transcript, sends the transcript to Gemini for
            summarization, and finally stores the transcript and summary in
            PostgreSQL.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-semibold">Where files live</h2>

          <p className="mt-4 leading-7 text-slate-600">
            Audio files are stored in a private Supabase Storage bucket. The
            database stores the note metadata, storage key, processing status,
            transcript, and summary.
          </p>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold">Supabase Storage</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Stores the original audio file using a generated storage key.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold">PostgreSQL</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Stores note metadata, status, progress, transcript, summary,
                errors, and the storage key.
              </p>
            </div>
          </div>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-semibold">Handling long audio</h2>

          <p className="mt-4 leading-7 text-slate-600">
            Large audio files are uploaded to cloud storage first instead of
            being passed through the backend as a large multipart request.
            Gnani's Batch API can consume an HTTPS cloud-storage URL, so the
            background task creates a temporary signed URL and gives that URL
            to Gnani.
          </p>

          <p className="mt-4 leading-7 text-slate-600">
            This keeps large files out of the synchronous request path and
            avoids making FastAPI responsible for transferring the complete
            audio file to the transcription service.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-semibold">
            Synchronous vs background work
          </h2>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold">Synchronous</h3>

              <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
                <li>• Receive the upload.</li>
                <li>• Store the audio file.</li>
                <li>• Create the database record.</li>
                <li>• Return the note ID to the frontend.</li>
              </ul>
            </div>

            <div className="rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold">Background</h3>

              <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
                <li>• Create and start the Gnani Batch job.</li>
                <li>• Poll the ASR job until completion.</li>
                <li>• Retrieve and save the transcript.</li>
                <li>• Generate and save the Gemini summary.</li>
                <li>• Update processing status and progress.</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-semibold">Progress and failures</h2>

          <p className="mt-4 leading-7 text-slate-600">
            Processing status is stored in PostgreSQL and exposed through the
            FastAPI API. The frontend polls for updates and shows states such
            as queued, uploading, transcribing, generating the summary,
            completed, and failed.
          </p>

          <p className="mt-4 leading-7 text-slate-600">
            Errors are also persisted so that API failures, invalid files, and
            other processing failures are visible to the user instead of
            leaving the interface in an indefinite loading state.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-semibold">
            What I would do differently with more time
          </h2>

          <p className="mt-4 leading-7 text-slate-600">
            For a larger production system, I would move background processing
            from FastAPI BackgroundTasks to a durable job queue such as
            Celery or another managed worker system. I would also add stronger
            observability, automated cleanup of old storage objects, and more
            robust handling for worker restarts and retries.
          </p>

          <p className="mt-4 leading-7 text-slate-600">
            I intentionally kept those components out of this take-home
            because the current system only needs a small, understandable
            processing pipeline.
          </p>
        </section>

        <section className="border-t border-slate-200 pt-8">
          <h2 className="text-2xl font-semibold">Repository</h2>

          <p className="mt-3 text-slate-600">
            Source code for this project:
          </p>

          <a
            href="https://github.com/Shreyam03/gnani-audio-notes"
            target="_blank"
            rel="noreferrer"
            className="mt-3 inline-block font-medium underline underline-offset-4"
          >
            View on GitHub →
          </a>
        </section>
      </div>
    </main>
  );
}