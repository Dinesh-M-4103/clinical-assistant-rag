import { z } from 'zod';
import { categorySchema } from '@/api/schemas';
import { MAX_UPLOAD_MB } from '@/lib/env';

const isPdf = (file: File) => file.type === 'application/pdf' || /\.pdf$/i.test(file.name);

/** Mirrors the server's upload rules so most mistakes are caught before the upload starts. */
export const reportUploadSchema = z.object({
  file: z
    .instanceof(File, { error: 'Choose a PDF file' })
    .refine(isPdf, 'Only PDF files are supported')
    .refine((file) => file.size > 0, 'This file is empty')
    .refine(
      (file) => file.size <= MAX_UPLOAD_MB * 1024 * 1024,
      `File is larger than ${MAX_UPLOAD_MB} MB`,
    ),
  name: z
    .string()
    .trim()
    .min(1, 'Give the report a name')
    .max(120, 'Keep the name under 120 characters'),
  category: categorySchema,
  notes: z.string().trim().max(1000, 'Keep notes under 1000 characters').optional(),
});

export type ReportUploadValues = z.infer<typeof reportUploadSchema>;

export function nameFromFilename(filename: string): string {
  return filename
    .replace(/\.pdf$/i, '')
    .replace(/[_-]+/g, ' ')
    .trim();
}
