"use client";

import { useRef } from "react";
import { MIN_NOTES_CHARS_FOR_TEXT_ONLY } from "@/types/backend";
import { useForm } from "./FormContext";
import NodeWrapper from "./NodeWrapper";

const NARRATIVE_ACCEPT =
  ".pdf,.md,.markdown,.txt,.text,.epub,.mp4,.webm,.mov,.mkv,.m4v,.avi";

function kindLabel(kind: string): string {
  switch (kind) {
    case "pdf":
      return "PDF";
    case "text":
      return "TEXT";
    case "book":
      return "BOOK";
    case "video":
      return "VIDEO";
    default:
      return kind.toUpperCase();
  }
}

export default function PolicyNode() {
  const {
    notesText,
    setNotesText,
    policySources,
    uploadingPolicySources,
    handlePolicyNarrativeFiles,
    removePolicySource,
  } = useForm();
  const narrativeRef = useRef<HTMLInputElement>(null);

  const notesOk = notesText.trim().length >= MIN_NOTES_CHARS_FOR_TEXT_ONLY;
  const readyHint =
    policySources.length > 0 || notesOk
      ? "\u2605 READY TO RUN"
      : `ADD FILE(S) OR ${MIN_NOTES_CHARS_FOR_TEXT_ONLY}+ CHARS BELOW`;

  return (
    <NodeWrapper
      badge="01"
      title="POLICY"
      description="Multimodal: PDF, Markdown, plain text, EPUB, video, and/or raw text — mix freely. CSV trends are separate."
      hasTarget={false}
    >
      <div
        className="nodrag nopan cursor-default space-y-3"
        style={{ width: 704 }}
      >
        <div className="space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <input
              ref={narrativeRef}
              type="file"
              accept={NARRATIVE_ACCEPT}
              onChange={handlePolicyNarrativeFiles}
              className="hidden"
              id="policy-narrative-node"
              data-testid="policy-narrative-input"
              multiple
            />
            <label
              htmlFor="policy-narrative-node"
              data-testid="upload-narrative-button"
              className="rpg-panel px-3 py-1.5 text-[13px] font-mono cursor-pointer transition-opacity hover:opacity-80"
              style={{
                color: uploadingPolicySources ? "#A0824A" : "#3D2510",
                background: "#E8D5A3",
                opacity: uploadingPolicySources ? 0.6 : 1,
              }}
            >
              {uploadingPolicySources
                ? "Uploading…"
                : "\u2191 Policy & documents"}
            </label>
            <span
              className="text-[12px] font-mono"
              style={{
                color:
                  policySources.length > 0 || notesOk ? "#3E7C34" : "#B83A52",
              }}
            >
              {readyHint}
            </span>
          </div>

          {policySources.length > 0 && (
            <div className="space-y-1">
              {policySources.map((source) => (
                <div
                  key={source.id}
                  className="flex items-start gap-2 rounded p-2 text-[12px] font-mono"
                  style={{
                    background: "#FFF8DC",
                    border: "1px solid #C4A46C",
                    color: "#6B4C2A",
                  }}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span style={{ color: "#3D2510" }}>{source.filename}</span>
                      <span
                        className="rounded px-1 text-[11px]"
                        style={{
                          background: "#E8D5A3",
                          color: "#5B3A1E",
                        }}
                      >
                        {kindLabel(source.kind)}
                      </span>
                    </div>
                    <div
                      className="mt-1 line-clamp-3 whitespace-pre-wrap"
                      style={{ color: "#8B7355" }}
                    >
                      {source.preview_text}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => removePolicySource(source.id)}
                    className="transition-opacity hover:opacity-60"
                    style={{ color: "#B83A52" }}
                    data-testid={`remove-policy-${source.id}`}
                  >
                    {"\u00D7"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="relative">
          <textarea
            value={notesText}
            onChange={(e) => setNotesText(e.target.value)}
            data-testid="policy-textarea"
            placeholder={`Raw text, instructions, or your full scenario (no upload required if you write at least ${MIN_NOTES_CHARS_FOR_TEXT_ONLY} characters). Combine with any files above.`}
            rows={10}
            className="rpg-panel w-full resize-none p-3 text-[15px] leading-relaxed font-mono outline-none transition-colors"
            style={{
              color: "#3D2510",
              background: "#FFF8DC",
              borderColor: notesText.length > 0 ? "#D4A520" : undefined,
            }}
          />
          <span
            className="absolute right-2 bottom-2 text-[12px] font-mono"
            style={{ color: "#A0824A" }}
          >
            {notesText.length} chars
            {!notesOk && policySources.length === 0 ? (
              <span style={{ color: "#B83A52" }}>
                {" "}
                ({MIN_NOTES_CHARS_FOR_TEXT_ONLY}+ for text-only)
              </span>
            ) : null}
          </span>
        </div>

      </div>
    </NodeWrapper>
  );
}
