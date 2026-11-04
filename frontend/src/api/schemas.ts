/**
 * Zod schemas for every payload in docs/api-contract.md. Types are inferred from them so the
 * runtime validation and the compile-time types can never drift apart.
 */
import { z } from 'zod';

export const CATEGORIES = [
  'lab',
  'imaging',
  'discharge',
  'prescription',
  'consultation',
  'other',
] as const;
export const GENDERS = ['male', 'female', 'other'] as const;

export const categorySchema = z.enum(CATEGORIES);
export const genderSchema = z.enum(GENDERS);

export const healthSchema = z.object({
  status: z.string(),
  llm_configured: z.boolean(),
  embedding_model: z.string().nullable().default(null),
  reranker_model: z.string().nullable().default(null),
  version: z.string(),
});

export const patientCreateSchema = z.object({
  uhid: z.string().regex(/^[A-Za-z0-9_-]{3,32}$/, 'Use 3–32 letters, digits, "-" or "_"'),
  name: z.string().trim().min(1, 'Enter the patient name').max(120),
  age: z
    .number({ error: 'Enter an age between 0 and 130' })
    .int('Enter a whole number')
    .min(0, 'Enter an age between 0 and 130')
    .max(130, 'Enter an age between 0 and 130'),
  gender: genderSchema,
  summary: z.string().trim().max(2000, 'Keep the summary under 2000 characters').optional(),
});

export const patientSchema = patientCreateSchema.omit({ summary: true }).extend({
  summary: z.string().nullable().default(null),
  report_count: z.number().int(),
  created_at: z.string(),
});

export const reportSchema = z.object({
  report_id: z.string(),
  uhid: z.string(),
  name: z.string(),
  category: categorySchema,
  notes: z.string().nullable().default(null),
  original_filename: z.string(),
  page_count: z.number().int(),
  chunk_count: z.number().int(),
  size_bytes: z.number().int(),
  uploaded_at: z.string(),
  file_url: z.string(),
});

export const citationSchema = z.object({
  id: z.string(),
  report_id: z.string(),
  report_name: z.string(),
  category: categorySchema,
  page: z.number().int(),
  section: z.string().nullable().default(null),
  text: z.string(),
  score: z.number(),
  cited: z.boolean(),
});

const rank = z.number().int().nullable().default(null);

export const traceSchema = z.object({
  intent: z.enum(['question', 'greeting', 'off_topic']),
  rewritten_query: z.string().nullable().default(null),
  insufficient_evidence: z.boolean(),
  candidates: z.array(
    z.object({
      id: z.string(),
      dense_rank: rank,
      bm25_rank: rank,
      fused_score: z.number(),
      rerank_score: z.number().nullable().default(null),
    }),
  ),
  timings_ms: z.object({
    rewrite: z.number().default(0),
    retrieval: z.number().default(0),
    rerank: z.number().default(0),
    generation: z.number().default(0),
    total: z.number().default(0),
  }),
  models: z.object({
    llm: z.string().nullable().default(null),
    embedding: z.string().nullable().default(null),
    reranker: z.string().nullable().default(null),
  }),
  tokens: z.object({ prompt: z.number(), completion: z.number() }).nullable().default(null),
});

export const chatResponseSchema = z.object({
  answer: z.string(),
  citations: z.array(citationSchema),
  trace: traceSchema,
});

export const errorEnvelopeSchema = z.object({
  error: z.object({ code: z.string(), message: z.string() }),
});

export type Category = z.infer<typeof categorySchema>;
export type Gender = z.infer<typeof genderSchema>;
export type Health = z.infer<typeof healthSchema>;
export type PatientCreate = z.infer<typeof patientCreateSchema>;
export type Patient = z.infer<typeof patientSchema>;
export type Report = z.infer<typeof reportSchema>;
export type Citation = z.infer<typeof citationSchema>;
export type Trace = z.infer<typeof traceSchema>;
export type ChatResponse = z.infer<typeof chatResponseSchema>;

export interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  question: string;
  history: ChatTurn[];
}
