import { AlertTriangle } from 'lucide-react';
import { Component, type ReactNode } from 'react';
import { EmptyState } from './EmptyState';
import { Button } from './ui/button';

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Changing this value clears a caught error (e.g. when the selected patient changes). */
  resetKey?: string;
}

interface ErrorBoundaryState {
  failed: boolean;
}

/** Keeps a rendering bug in one panel from blanking the whole app. */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { failed: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { failed: true };
  }

  componentDidUpdate(previous: ErrorBoundaryProps): void {
    if (this.state.failed && previous.resetKey !== this.props.resetKey) {
      this.setState({ failed: false });
    }
  }

  render(): ReactNode {
    if (!this.state.failed) return this.props.children;
    return (
      <EmptyState
        icon={<AlertTriangle className="size-5" />}
        title="Something went wrong"
        description="This section hit an unexpected error. Your data is safe."
        action={<Button onClick={() => this.setState({ failed: false })}>Try again</Button>}
      />
    );
  }
}
