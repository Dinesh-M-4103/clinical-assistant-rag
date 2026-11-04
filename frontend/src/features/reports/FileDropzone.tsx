import { FileText, UploadCloud } from 'lucide-react';
import { useState, type DragEvent } from 'react';
import { cn } from '@/lib/cn';
import { formatBytes } from '@/lib/format';

interface FileDropzoneProps {
  id: string;
  file: File | undefined;
  onFile: (file: File) => void;
  describedBy?: string;
  invalid?: boolean;
  disabled?: boolean;
}

/** Click-to-browse or drag-and-drop target; the real `<input type="file">` stays keyboard-focusable. */
export function FileDropzone({
  id,
  file,
  onFile,
  describedBy,
  invalid,
  disabled,
}: FileDropzoneProps) {
  const [dragging, setDragging] = useState(false);

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files[0];
    if (dropped && !disabled) onFile(dropped);
  };

  return (
    <label
      htmlFor={id}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={cn(
        'flex min-h-28 cursor-pointer flex-col items-center justify-center gap-1.5 rounded-lg border-2 border-dashed px-4 py-5 text-center transition-colors focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-surface hover:border-primary/60 hover:bg-primary-soft/40',
        dragging ? 'border-primary bg-primary-soft/60' : 'border-border',
        invalid && 'border-danger',
        disabled && 'pointer-events-none opacity-60',
      )}
    >
      <input
        id={id}
        type="file"
        accept="application/pdf,.pdf"
        disabled={disabled}
        aria-describedby={describedBy}
        aria-invalid={invalid}
        className="sr-only"
        onChange={(event) => {
          const chosen = event.target.files?.[0];
          if (chosen) onFile(chosen);
          event.target.value = '';
        }}
      />
      {file ? (
        <>
          <FileText aria-hidden className="size-6 text-primary-text" />
          <span className="max-w-full truncate text-sm font-medium">{file.name}</span>
          <span className="text-xs tabular-nums text-muted">
            {formatBytes(file.size)} · click to replace
          </span>
        </>
      ) : (
        <>
          <UploadCloud aria-hidden className="size-6 text-muted" />
          <span className="text-sm font-medium">Drop a PDF here or click to browse</span>
          <span className="text-xs text-muted">PDF only</span>
        </>
      )}
    </label>
  );
}
