import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog';
import { InspectorPanel } from './InspectorPanel';
import { useWorkspace } from './workspaceStore';

/** Tablet-width slide-over holding the inspector; desktop shows it inline instead. */
export function InspectorSheet({ uhid }: { uhid: string }) {
  const open = useWorkspace((state) => state.inspectorOpen);
  const close = useWorkspace((state) => state.closeInspector);
  return (
    <Dialog open={open} onOpenChange={(next) => !next && close()}>
      <DialogContent placement="right" hideClose>
        <DialogTitle className="sr-only">Inspector</DialogTitle>
        <DialogDescription className="sr-only">
          Evidence, reports and trace for the selected answer.
        </DialogDescription>
        <InspectorPanel uhid={uhid} onClose={close} />
      </DialogContent>
    </Dialog>
  );
}
