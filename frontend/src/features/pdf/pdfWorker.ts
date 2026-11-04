import { pdfjs } from 'react-pdf';

/** The worker is bundled from node_modules (no CDN), so the viewer also works offline. */
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();
