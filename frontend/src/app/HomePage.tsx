import { Stethoscope, UserPlus } from 'lucide-react';
import { EmptyState } from '@/components/EmptyState';
import { Button } from '@/components/ui/button';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { PatientList } from '@/features/patients/PatientList';
import { useWorkspace } from '@/features/workspace/workspaceStore';

/** Landing view. Phones have no sidebar, so the patient list is shown here directly. */
export function HomePage() {
  const mobile = useBreakpoint() === 'mobile';
  const setAddPatientOpen = useWorkspace((state) => state.setAddPatientOpen);

  if (mobile) {
    return (
      <div className="flex min-h-0 flex-1 flex-col gap-4 px-3 py-5">
        <div className="px-2">
          <h1 className="text-lg font-semibold">Patients</h1>
          <p className="text-sm text-muted">Choose a patient to open their records.</p>
        </div>
        <PatientList className="flex-1" />
        <div className="px-1 pb-[env(safe-area-inset-bottom)]">
          <Button variant="primary" className="w-full" onClick={() => setAddPatientOpen(true)}>
            <UserPlus className="size-4" /> Add patient
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <EmptyState
        icon={<Stethoscope className="size-6" />}
        title="Select a patient"
        description="Pick someone from the list to chat with their reports, or add a new patient to upload records."
        action={
          <Button variant="primary" onClick={() => setAddPatientOpen(true)}>
            <UserPlus className="size-4" /> Add patient
          </Button>
        }
      />
    </div>
  );
}
