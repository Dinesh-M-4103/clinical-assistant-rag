import { QueryClientProvider } from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';
import { Toaster } from 'sonner';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { useTheme } from '@/hooks/useTheme';
import { createQueryClient } from './queryClient';

function ThemedToaster() {
  const { resolved } = useTheme();
  const mobile = useBreakpoint() === 'mobile';
  return (
    <Toaster
      theme={resolved}
      position={mobile ? 'top-center' : 'bottom-right'}
      toastOptions={{
        classNames: {
          toast: '!rounded-lg !border-border !bg-surface !text-foreground !shadow-float !font-sans',
          description: '!text-muted',
        },
      }}
    />
  );
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient);
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        {children}
        <ThemedToaster />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
