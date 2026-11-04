import { Menu, UserPlus } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { usePatients } from '@/api/hooks/patients';
import { Brand } from '@/components/Brand';
import { ThemeToggle } from '@/components/ThemeToggle';
import { IconButton } from '@/components/ui/icon-button';
import { cn } from '@/lib/cn';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { PatientAvatar } from './PatientAvatar';

/** Tablet navigation: a slim icon rail whose menu button opens the full patient drawer. */
export function PatientRail() {
  const { data: patients } = usePatients();
  const setDrawerOpen = useWorkspace((state) => state.setPatientDrawerOpen);
  const setAddPatientOpen = useWorkspace((state) => state.setAddPatientOpen);

  return (
    <div className="flex h-full w-[72px] shrink-0 flex-col items-center gap-3 border-r border-border bg-surface py-4">
      <Brand compact />
      <IconButton
        label="Open patient list"
        icon={<Menu className="size-5" />}
        onClick={() => setDrawerOpen(true)}
      />
      <nav
        aria-label="Patients"
        className="flex min-h-0 flex-1 flex-col items-center gap-2 overflow-y-auto px-2 py-1"
      >
        {patients?.map((patient) => (
          <NavLink
            key={patient.uhid}
            to={`/patients/${encodeURIComponent(patient.uhid)}`}
            aria-label={`${patient.name}, ${patient.uhid}`}
            title={`${patient.name} (${patient.uhid})`}
            className={({ isActive }) =>
              cn(
                'rounded-full p-0.5 ring-2 ring-transparent transition-shadow hover:ring-border',
                isActive && 'ring-primary hover:ring-primary',
              )
            }
          >
            <PatientAvatar name={patient.name} />
          </NavLink>
        ))}
      </nav>
      <IconButton
        label="Add patient"
        icon={<UserPlus className="size-5" />}
        onClick={() => setAddPatientOpen(true)}
      />
      <ThemeToggle />
    </div>
  );
}
