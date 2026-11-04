import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog';
import { PatientSidebar } from '@/features/patients/PatientSidebar';
import { useWorkspace } from '@/features/workspace/workspaceStore';

/** Full patient list as a left drawer for tablet and phone widths. */
export function PatientDrawer() {
  const open = useWorkspace((state) => state.patientDrawerOpen);
  const setOpen = useWorkspace((state) => state.setPatientDrawerOpen);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent placement="left" hideClose className="max-w-[min(20rem,88vw)]">
        <DialogTitle className="sr-only">Patients</DialogTitle>
        <DialogDescription className="sr-only">
          Choose a patient or add a new one.
        </DialogDescription>
        <PatientSidebar onNavigate={() => setOpen(false)} onClose={() => setOpen(false)} />
      </DialogContent>
    </Dialog>
  );
}
