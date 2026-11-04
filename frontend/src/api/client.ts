import type { z } from 'zod';
import { API_ORIGIN } from '@/lib/env';
import { errorEnvelopeSchema } from './schemas';

/** Failure of an API call, normalised from the contract's `{error: {code, message}}` envelope. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  /** True when the server could not be reached at all (as opposed to answering with an error). */
  get isNetwork(): boolean {
    return this.status === 0;
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'DELETE';
  json?: unknown;
  form?: FormData;
  signal?: AbortSignal;
  accept?: string;
}

async function errorFromResponse(response: Response): Promise<ApiError> {
  const body: unknown = await response.json().catch(() => null);
  const envelope = errorEnvelopeSchema.safeParse(body);
  if (envelope.success) {
    const { code, message } = envelope.data.error;
    return new ApiError(response.status, code, message);
  }
  return new ApiError(response.status, 'http_error', `Request failed (${response.status}).`);
}

/** Performs the request and returns the raw response, throwing `ApiError` for any failure. */
export async function send(path: string, options: RequestOptions = {}): Promise<Response> {
  const headers = new Headers();
  if (options.accept) headers.set('Accept', options.accept);
  if (options.json !== undefined) headers.set('Content-Type', 'application/json');

  let response: Response;
  try {
    response = await fetch(`${API_ORIGIN}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.form ?? (options.json === undefined ? undefined : JSON.stringify(options.json)),
      signal: options.signal,
    });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new ApiError(
      0,
      'network_error',
      'Cannot reach the server. Check that the backend is running.',
    );
  }
  if (!response.ok) throw await errorFromResponse(response);
  return response;
}

/** Fetches JSON and validates it against `schema`; the parsed value is what callers receive. */
export async function requestJson<S extends z.ZodType>(
  path: string,
  schema: S,
  options?: RequestOptions,
): Promise<z.output<S>> {
  const response = await send(path, { accept: 'application/json', ...options });
  const parsed = schema.safeParse(await response.json().catch(() => null));
  if (!parsed.success) {
    throw new ApiError(502, 'invalid_response', 'The server sent an unexpected response.');
  }
  return parsed.data;
}

export async function requestVoid(path: string, options?: RequestOptions): Promise<void> {
  await send(path, options);
}

export async function requestBlob(path: string, options?: RequestOptions): Promise<Blob> {
  const response = await send(path, options);
  return response.blob();
}
