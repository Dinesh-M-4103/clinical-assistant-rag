import { MutationCache, QueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ApiError } from '@/api/client';
import { describeError } from '@/lib/errors';

declare module '@tanstack/react-query' {
  interface Register {
    mutationMeta: { silent?: boolean };
  }
}

/** Client errors (4xx) will not fix themselves, so only transient failures are retried. */
const shouldRetry = (failures: number, error: Error) =>
  failures < 1 && !(error instanceof ApiError && error.status >= 400 && error.status < 500);

/** Every failed mutation toasts the server's message unless the caller shows it inline (`meta.silent`). */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: shouldRetry, refetchOnWindowFocus: false, staleTime: 15_000 },
    },
    mutationCache: new MutationCache({
      onError: (error, _variables, _context, mutation) => {
        if (!mutation.meta?.silent) toast.error(describeError(error));
      },
    }),
  });
}
