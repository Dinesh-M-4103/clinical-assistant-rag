import { useQuery } from '@tanstack/react-query';
import { api } from '../endpoints';
import { queryKeys } from './keys';

const HEALTHY_POLL_MS = 30_000;
const DOWN_POLL_MS = 5_000;

/** Polls `/health`, backing off to a faster cadence while the backend is unreachable. */
export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: api.health,
    retry: false,
    refetchInterval: (query) => (query.state.status === 'error' ? DOWN_POLL_MS : HEALTHY_POLL_MS),
  });
}
