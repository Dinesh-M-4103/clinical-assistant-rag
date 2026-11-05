import { PanelRight, Trash2, Upload } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDeletePatient } from '@/api/hooks/patients';
import type { Patient } from '@/api/schemas';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { IconButton } from '@/components/ui/icon-button';
import { Skeleton } from '@/components/ui/skeleton';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { useChatStore } from '@/features/chat/chatStore';
import { useWorkspace } from '@/features/workspace/workspaceStore';
import { PatientAvatar } from './PatientAvatar';

export function PatientHeaderSkeleton() {
  return (
    <div
      className="flex items-center gap-3 border-b border-border bg-surface px-4 py-3"
      role="status"
      aria-label="Loading patient"
    >
      <Skeleton className="size-11 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  );
}

export function PatientHeader({ patient }: { patient: Patient }) {
  const navigate = useNavigate();
  const breakpoint = useBreakpoint();
  const deletePatient = useDeletePatient();
  const clearChat = useChatStore((state) => state.clear);
  const setUploadOpen = useWorkspace((state) => state.setUploadOpen);
  const openInspector = useWorkspace((state) => state.openInspector);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const remove = () =>
    deletePatient.mutate(patient.uhid, {
      onSuccess: () => {
        clearChat(patient.uhid);
        setConfirmOpen(false);
        navigate('/');
      },
    });

  return (
    <header className="border-b border-border bg-surface px-4 py-3 md:px-6">
      <div className="mx-auto flex w-full max-w-3xl items-start gap-3 md:gap-4">
        <PatientAvatar name={patient.name} className="size-11 max-sm:hidden" />
        <div className="min-w-0 flex-1">
          <h1
            className="truncate text-base font-semibold leading-tight md:text-lg"
            title={patient.name}
          >
            {patient.name}
          </h1>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <Badge className="tabular-nums">UHID {patient.uhid}</Badge>
            <Badge>{patient.age} yrs</Badge>
            <Badge className="capitalize">{patient.gender}</Badge>
          </div>
          {patient.summary && (
            <p className="mt-2 line-clamp-1 max-w-2xl text-[13px] leading-snug text-muted sm:line-clamp-2">
              {patient.summary}
            </p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setUploadOpen(true)}
            className="max-md:hidden"
          >
            <Upload className="size-4" /> Upload report
          </Button>
          <IconButton
            label="Upload report"
            icon={<Upload className="size-[18px]" />}
            onClick={() => setUploadOpen(true)}
            className="md:hidden"
          />
          {breakpoint === 'tablet' && (
            <IconButton
              label="Open inspector"
              icon={<PanelRight className="size-[18px]" />}
              onClick={() => openInspector('evidence')}
            />
          )}
          <IconButton
            label={`Delete ${patient.name}`}
            icon={<Trash2 className="size-[18px]" />}
            onClick={() => setConfirmOpen(true)}
            className="hover:text-danger"
          />
        </div>
      </div>
      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title={`Delete ${patient.name}?`}
        description="This permanently removes the patient, all uploaded reports and their search index. This cannot be undone."
        confirmLabel="Delete patient"
        pending={deletePatient.isPending}
        onConfirm={remove}
      />
    </header>
  );
}
