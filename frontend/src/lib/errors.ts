import { ApiError } from '@/api/client';

/** Human-readable text for any thrown value, preferring the server's own message. */
export function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error && error.message) return error.message;
  return 'Something went wrong. Please try again.';
}
