import { Search, UserPlus, Users } from 'lucide-react';
import { useMemo, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { usePatients } from '@/api/hooks/patients';
import type { Patient } from '@/api/schemas';
import { EmptyState } from '@/components/EmptyState';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/field';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/cn';
import { pluralize } from '@/lib/format';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { PatientAvatar } from './PatientAvatar';
import { matchesQuery } from './search';

function PatientRow({ patient, onNavigate }: { patient: Patient; onNavigate?: () => void }) {
  return (
    <NavLink
      to={`/patients/${encodeURIComponent(patient.uhid)}`}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          'flex min-h-14 items-center gap-3 rounded-md px-2.5 py-2 transition-colors hover:bg-subtle',
          isActive && 'bg-primary-soft hover:bg-primary-soft',
        )
      }
    >
      <PatientAvatar name={patient.name} />
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{patient.name}</span>
        <span className="block truncate text-xs tabular-nums text-muted">
          {patient.uhid} · {pluralize(patient.report_count, 'report')}
        </span>
      </span>
    </NavLink>
  );
}

function ListSkeleton() {
  return (
    <div className="space-y-2 p-1" role="status" aria-label="Loading patients">
      {Array.from({ length: 5 }, (_, index) => (
        <div key={index} className="flex items-center gap-3 px-2.5 py-2">
          <Skeleton className="size-10 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3.5 w-2/3" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

interface PatientListProps {
  onNavigate?: () => void;
  className?: string;
}

/** Searchable patient list shared by the sidebar, the drawer and the mobile home screen. */
export function PatientList({ onNavigate, className }: PatientListProps) {
  const { data: patients, isPending, isError, refetch } = usePatients();
  const setAddPatientOpen = useWorkspace((state) => state.setAddPatientOpen);
  const [query, setQuery] = useState('');
  const visible = useMemo(
    () => patients?.filter((patient) => matchesQuery(patient, query)) ?? [],
    [patients, query],
  );

  return (
    <div className={cn('flex min-h-0 flex-col gap-3', className)}>
      <div className="relative px-1">
        <Search
          aria-hidden
          className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted"
        />
        <Input
          type="search"
          aria-label="Search patients"
          placeholder="Search name or UHID"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="pl-9"
        />
      </div>

      <nav aria-label="Patients" className="min-h-0 flex-1 overflow-y-auto px-1">
        {isPending ? (
          <ListSkeleton />
        ) : isError ? (
          <EmptyState
            icon={<Users className="size-5" />}
            title="Couldn't load patients"
            action={<Button onClick={() => void refetch()}>Retry</Button>}
          />
        ) : visible.length > 0 ? (
          <ul className="space-y-1">
            {visible.map((patient) => (
              <li key={patient.uhid}>
                <PatientRow patient={patient} onNavigate={onNavigate} />
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={<Users className="size-5" />}
            title={query ? 'No matching patients' : 'No patients yet'}
            description={query ? 'Try a different name or UHID.' : 'Add a patient to get started.'}
            className="py-8"
            action={
              query ? undefined : (
                <Button variant="primary" onClick={() => setAddPatientOpen(true)}>
                  <UserPlus className="size-4" /> Add patient
                </Button>
              )
            }
          />
        )}
      </nav>
    </div>
  );
}
