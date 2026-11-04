import { AlertTriangle, WifiOff } from 'lucide-react';
import { useHealth } from '@/api/hooks/health';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import { API_ORIGIN } from '@/lib/env';

/** Backend-down and LLM-not-configured warnings; /health keeps polling so recovery is automatic. */
export function HealthBanner() {
  const { data, isError, isFetching, refetch } = useHealth();

  if (isError) {
    return (
      <div
        role="alert"
        className="flex flex-wrap items-center gap-x-3 gap-y-1 bg-danger-soft px-4 py-2 text-sm text-danger"
      >
        <WifiOff aria-hidden className="size-4 shrink-0" />
        <span className="min-w-0 flex-1">
          Can&rsquo;t reach the backend at {API_ORIGIN}. Retrying automatically.
        </span>
        <Button
          variant="secondary"
          size="sm"
          className="md:h-8"
          onClick={() => void refetch()}
          disabled={isFetching}
        >
          {isFetching && <Spinner />}
          Retry now
        </Button>
      </div>
    );
  }
  if (data && !data.llm_configured) {
    return (
      <div
        role="status"
        className="flex items-center gap-3 bg-warning-soft px-4 py-2 text-sm text-warning"
      >
        <AlertTriangle aria-hidden className="size-4 shrink-0" />
        <span>
          The language model isn&rsquo;t configured, so questions can&rsquo;t be answered yet.
        </span>
      </div>
    );
  }
  return null;
}
