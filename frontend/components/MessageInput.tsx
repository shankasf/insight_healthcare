"use client";

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useLayoutEffect,
  useRef,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { SendHorizonal } from "lucide-react";

interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  disabled: boolean;
}

export interface MessageInputHandle {
  focus: () => void;
}

const MAX_TEXTAREA_HEIGHT = 140; // ~5 lines at default line-height

const MessageInput = forwardRef<MessageInputHandle, MessageInputProps>(function MessageInput(
  { value, onChange, onSubmit, disabled },
  ref,
) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useImperativeHandle(ref, () => ({
    focus: () => textareaRef.current?.focus(),
  }));

  // Auto-grow the textarea up to MAX_TEXTAREA_HEIGHT, then scroll inside.
  useLayoutEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const next = Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT);
    el.style.height = `${next}px`;
    el.style.overflowY = el.scrollHeight > MAX_TEXTAREA_HEIGHT ? "auto" : "hidden";
  }, [value]);

  // Restore focus to the input after a send completes.
  useEffect(() => {
    if (!disabled) textareaRef.current?.focus();
  }, [disabled]);

  function trySubmit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      trySubmit();
    }
  }

  function handleFormSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    trySubmit();
  }

  const canSend = value.trim().length > 0 && !disabled;

  return (
    <form
      onSubmit={handleFormSubmit}
      className="border-t border-gray-200 bg-white px-3 py-3 sm:px-6 sm:py-4"
    >
      <div
        className={[
          "mx-auto flex w-full max-w-[720px] items-end gap-2 rounded-2xl border bg-white px-3 py-2 shadow-sm transition",
          disabled
            ? "border-gray-200 opacity-80"
            : "border-gray-300 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100",
        ].join(" ")}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          placeholder="Type your message..."
          aria-label="Message"
          className="flex-1 resize-none border-0 bg-transparent text-sm leading-6 text-gray-900 placeholder:text-gray-400 focus:outline-none disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          disabled={!canSend}
          aria-label="Send message"
          className={[
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition",
            canSend
              ? "bg-blue-600 text-white hover:bg-blue-700 active:scale-95"
              : "bg-gray-100 text-gray-400",
          ].join(" ")}
        >
          <SendHorizonal className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
      <p className="mx-auto mt-2 max-w-[720px] px-1 text-[11px] text-gray-400">
        Press Enter to send, Shift + Enter for a new line.
      </p>
    </form>
  );
});

export default MessageInput;
