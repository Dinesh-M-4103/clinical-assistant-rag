import { Outlet } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { AddPatientDialog } from '@/features/patients/AddPatientDialog';
import { PatientRail } from '@/features/patients/PatientRail';
import { PatientSidebar } from '@/features/patients/PatientSidebar';
import { HealthBanner } from './HealthBanner';
import { MobileTopBar } from './MobileTopBar';
import { PatientDrawer } from './PatientDrawer';

/**
 * Responsive frame: sidebar (>=1280), icon rail (768-1279) or top bar (<768) around the routed page.
 * Capped at 2000px so ultra-wide screens keep readable line lengths.
 */
export function AppShell() {
  const breakpoint = useBreakpoint();
  return (
    <div className="mx-auto flex h-dvh max-w-[2000px] flex-col overflow-hidden bg-background min-[2000px]:border-x min-[2000px]:border-border">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-[70] focus:rounded-md focus:bg-surface focus:px-3 focus:py-2 focus:shadow-float"
      >
        Skip to content
      </a>
      <HealthBanner />
      {breakpoint === 'mobile' && <MobileTopBar />}
      <div className="flex min-h-0 flex-1">
        {breakpoint === 'desktop' && (
          <aside aria-label="Patients" className="w-72 shrink-0 border-r border-border">
            <PatientSidebar />
          </aside>
        )}
        {breakpoint === 'tablet' && <PatientRail />}
        <main
          id="main"
          className="flex min-h-0 min-w-0 flex-1 flex-col focus:outline-none"
          tabIndex={-1}
        >
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
      {breakpoint !== 'desktop' && <PatientDrawer />}
      <AddPatientDialog />
    </div>
  );
}
