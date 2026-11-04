import { Monitor, Moon, Sun } from 'lucide-react';
import { IconButton } from '@/components/ui/icon-button';
import { useTheme } from '@/hooks/useTheme';

const ICONS = { system: Monitor, light: Sun, dark: Moon } as const;
const NEXT_LABEL = { system: 'light', light: 'dark', dark: 'system' } as const;

/** Cycles system -> light -> dark; the label states the current mode and what a click does. */
export function ThemeToggle() {
  const { preference, cycle } = useTheme();
  const Icon = ICONS[preference];
  return (
    <IconButton
      label={`Theme: ${preference}. Switch to ${NEXT_LABEL[preference]}`}
      icon={<Icon className="size-[18px]" />}
      onClick={cycle}
    />
  );
}
