import { UserPlus, X } from 'lucide-react';
import { Brand } from '@/components/Brand';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Button } from '@/components/ui/button';
import { IconButton } from '@/components/ui/icon-button';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { PatientList } from './PatientList';

interface PatientSidebarProps {
  /** Called after a patient is chosen, so a drawer can close itself. */
  onNavigate?: () => void;
  /** Present when the sidebar is shown inside a drawer. */
  onClose?: () => void;
}

/** Full patient navigation; used as the desktop sidebar and inside the tablet/mobile drawer. */
export function PatientSidebar({ onNavigate, onClose }: PatientSidebarProps) {
  const setAddPatientOpen = useWorkspace((state) => state.setAddPatientOpen);
  const addPatient = () => {
    onClose?.();
    setAddPatientOpen(true);
  };

  return (
    <div className="flex h-full min-h-0 flex-col gap-4 bg-surface py-4">
      <div className="flex items-center justify-between px-4">
        <Brand />
        <div className="flex items-center">
          <ThemeToggle />
          {onClose && (
            <IconButton
              label="Close patient list"
              icon={<X className="size-[18px]" />}
              onClick={onClose}
            />
          )}
        </div>
      </div>
      <PatientList onNavigate={onNavigate} className="flex-1 px-2" />
      <div className="px-4 pb-[env(safe-area-inset-bottom)]">
        <Button variant="primary" className="w-full" onClick={addPatient}>
          <UserPlus className="size-4" /> Add patient
        </Button>
      </div>
    </div>
  );
}
