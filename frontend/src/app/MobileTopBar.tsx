import { Menu } from 'lucide-react';
import { Brand } from '@/components/Brand';
import { ThemeToggle } from '@/components/ThemeToggle';
import { IconButton } from '@/components/ui/icon-button';
import { useWorkspace } from '@/features/workspace/workspaceStore';

export function MobileTopBar() {
  const setDrawerOpen = useWorkspace((state) => state.setPatientDrawerOpen);
  return (
    <header className="flex items-center justify-between border-b border-border bg-surface px-2 pt-[env(safe-area-inset-top)]">
      <div className="flex items-center gap-1">
        <IconButton
          label="Open patient list"
          icon={<Menu className="size-5" />}
          onClick={() => setDrawerOpen(true)}
        />
        <Brand />
      </div>
      <ThemeToggle />
    </header>
  );
}
