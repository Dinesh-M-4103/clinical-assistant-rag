import { create } from 'zustand';
import { rememberOpener } from '@/lib/focus';

export type InspectorTab = 'evidence' | 'reports' | 'trace';

/** A PDF page the clinician asked to see, optionally with the cited passage to highlight. */
export interface PdfTarget {
  uhid: string;
  reportId: string;
  reportName: string;
  fileUrl: string;
  page: number;
  highlight: string | null;
}

interface WorkspaceState {
  inspectorTab: InspectorTab;
  /** Tablet: the slide-over is open. Mobile: the inspector replaces the chat. Desktop: ignored. */
  inspectorOpen: boolean;
  patientDrawerOpen: boolean;
  addPatientOpen: boolean;
  uploadOpen: boolean;
  pdf: PdfTarget | null;
  openInspector: (tab: InspectorTab) => void;
  setInspectorTab: (tab: InspectorTab) => void;
  closeInspector: () => void;
  setPatientDrawerOpen: (open: boolean) => void;
  setAddPatientOpen: (open: boolean) => void;
  setUploadOpen: (open: boolean) => void;
  openPdf: (target: PdfTarget) => void;
  closePdf: () => void;
}

export const useWorkspace = create<WorkspaceState>((set) => ({
  inspectorTab: 'evidence',
  inspectorOpen: false,
  patientDrawerOpen: false,
  addPatientOpen: false,
  uploadOpen: false,
  pdf: null,
  openInspector: (tab) => {
    rememberOpener();
    set({ inspectorTab: tab, inspectorOpen: true });
  },
  setInspectorTab: (inspectorTab) => set({ inspectorTab }),
  closeInspector: () => set({ inspectorOpen: false }),
  setPatientDrawerOpen: (patientDrawerOpen) => {
    if (patientDrawerOpen) rememberOpener();
    set({ patientDrawerOpen });
  },
  setAddPatientOpen: (addPatientOpen) => {
    if (addPatientOpen) rememberOpener();
    set({ addPatientOpen });
  },
  setUploadOpen: (uploadOpen) => {
    if (uploadOpen) rememberOpener();
    set({ uploadOpen });
  },
  openPdf: (pdf) => {
    rememberOpener();
    set({ pdf });
  },
  closePdf: () => set({ pdf: null }),
}));
