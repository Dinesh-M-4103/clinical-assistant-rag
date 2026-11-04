import type { ChatResponse, Citation, Report, Trace } from '@/api/schemas';

/** Passage text intentionally mirrors the lines in public/mock/sample-report.pdf so highlights can match. */
const PASSAGES = {
  hba1c: {
    page: 1,
    section: 'Laboratory Results',
    text: 'HbA1c 7.8 % (reference 4.0 - 5.6 %) collected 12 Sep 2026',
  },
  glucose: {
    page: 1,
    section: 'Laboratory Results',
    text: 'Fasting plasma glucose 148 mg/dL (reference 70 - 99 mg/dL)',
  },
  ldl: {
    page: 2,
    section: 'Lipid Profile',
    text: 'Total cholesterol 214 mg/dL (desirable below 200). LDL cholesterol 138 mg/dL (optimal below 100). HDL cholesterol 44 mg/dL. Triglycerides 182 mg/dL (normal below 150)',
  },
  kidney: {
    page: 2,
    section: 'Renal Function',
    text: 'Serum creatinine 1.1 mg/dL. eGFR 68 mL/min/1.73 m2',
  },
  meds: {
    page: 3,
    section: 'Prescription',
    text: 'Metformin 500 mg twice daily with meals. Atorvastatin 20 mg at night. Amlodipine 5 mg once daily',
  },
  impression: {
    page: 3,
    section: 'Impression',
    text: 'Poor glycaemic control. Recommend dietary review and repeat HbA1c in 3 months.',
  },
} as const;

type PassageKey = keyof typeof PASSAGES;

interface Script {
  intent: Trace['intent'];
  answer: string;
  /** Retrieved passages in rank order; `cited` marks the ones the answer references. */
  retrieved: { key: PassageKey; cited: boolean }[];
  insufficient?: boolean;
}

const SCRIPTS: { matches: RegExp; script: Script }[] = [
  {
    matches: /\b(hello|hi|hey|thanks|thank you)\b/i,
    script: {
      intent: 'greeting',
      answer:
        'Hello! Ask me anything about this patient’s uploaded reports and I’ll answer with citations.',
      retrieved: [],
    },
  },
  {
    matches: /hba1c|a1c|glyc/i,
    script: {
      intent: 'question',
      answer:
        'The most recent **HbA1c is 7.8 %**, collected on 12 Sep 2026 [C1]. That is above the 5.6 % upper reference limit, and fasting glucose was also raised at 148 mg/dL [C2].\n\n| Test | Result | Reference |\n| --- | --- | --- |\n| HbA1c | 7.8 % | 4.0 - 5.6 % |\n| Fasting glucose | 148 mg/dL | 70 - 99 mg/dL |\n\nThe reviewing clinician noted poor glycaemic control and advised repeating the HbA1c in 3 months [C3].',
      retrieved: [
        { key: 'hba1c', cited: true },
        { key: 'glucose', cited: true },
        { key: 'impression', cited: true },
        { key: 'ldl', cited: false },
        { key: 'kidney', cited: false },
      ],
    },
  },
  {
    matches: /range|abnormal|lab|result/i,
    script: {
      intent: 'question',
      answer:
        'Several values are outside the reference range:\n\n- **HbA1c** 7.8 % (reference 4.0 - 5.6 %) [C1]\n- **Fasting glucose** 148 mg/dL (reference 70 - 99 mg/dL) [C2]\n- **LDL cholesterol** 138 mg/dL (optimal below 100) and **triglycerides** 182 mg/dL (normal below 150) [C3]\n\nRenal function was within normal limits.',
      retrieved: [
        { key: 'hba1c', cited: true },
        { key: 'glucose', cited: true },
        { key: 'ldl', cited: true },
        { key: 'kidney', cited: false },
      ],
    },
  },
  {
    matches: /summar|diagnos|history|overview/i,
    script: {
      intent: 'question',
      answer:
        '### Key findings\n\n1. **Type 2 diabetes** with poor glycaemic control (HbA1c 7.8 %) [C1][C2].\n2. **Dyslipidaemia**: raised LDL and triglycerides with low HDL [C3].\n3. Kidney function is preserved (eGFR 68) [C4].\n\nA dietary review and repeat HbA1c in 3 months were recommended [C5].',
      retrieved: [
        { key: 'hba1c', cited: true },
        { key: 'glucose', cited: true },
        { key: 'ldl', cited: true },
        { key: 'kidney', cited: true },
        { key: 'impression', cited: true },
      ],
    },
  },
  {
    matches: /medic|drug|dose|prescri/i,
    script: {
      intent: 'question',
      answer:
        'Current medications on the latest prescription:\n\n- **Metformin** 500 mg twice daily with meals [C1]\n- **Atorvastatin** 20 mg at night [C1]\n- **Amlodipine** 5 mg once daily [C1]',
      retrieved: [
        { key: 'meds', cited: true },
        { key: 'impression', cited: false },
      ],
    },
  },
];

const NO_EVIDENCE: Script = {
  intent: 'question',
  answer: 'I couldn’t find that in this patient’s uploaded records, so I can’t answer it reliably.',
  retrieved: [],
  insufficient: true,
};

export function pickScript(question: string, hasReports: boolean): Script {
  if (!hasReports) return NO_EVIDENCE;
  return SCRIPTS.find(({ matches }) => matches.test(question))?.script ?? NO_EVIDENCE;
}

function buildCitations(script: Script, reports: Report[]): Citation[] {
  const report = reports[0];
  if (!report) return [];
  return script.retrieved.map(({ key, cited }, index) => ({
    id: `C${index + 1}`,
    report_id: report.report_id,
    report_name: report.name,
    category: report.category,
    page: PASSAGES[key].page,
    section: PASSAGES[key].section,
    text: PASSAGES[key].text,
    score: Number((0.92 - index * 0.11).toFixed(2)),
    cited,
  }));
}

function buildTrace(script: Script, question: string, citations: Citation[]): Trace {
  const searched = script.intent === 'question';
  return {
    intent: script.intent,
    rewritten_query: searched ? question.replace(/\?$/, '').trim() : null,
    insufficient_evidence: script.insufficient ?? false,
    candidates: citations.map((citation, index) => ({
      id: citation.id,
      dense_rank: index + 1,
      bm25_rank: index === 1 ? null : ((index + 2) % citations.length) + 1,
      fused_score: Number((0.033 - index * 0.004).toFixed(3)),
      rerank_score: Number((0.94 - index * 0.17).toFixed(3)),
    })),
    timings_ms: searched
      ? { rewrite: 212, retrieval: 38, rerank: 124, generation: 1380, total: 1768 }
      : { rewrite: 0, retrieval: 0, rerank: 0, generation: 240, total: 242 },
    models: {
      llm: 'gemini-2.5-flash',
      embedding: searched ? 'BAAI/bge-small-en-v1.5' : null,
      reranker: searched ? 'cross-encoder/ms-marco-MiniLM-L-6-v2' : null,
    },
    tokens: script.insufficient ? null : { prompt: 1204, completion: 186 },
  };
}

export function buildResponse(script: Script, question: string, reports: Report[]): ChatResponse {
  const citations = buildCitations(script, reports);
  return { answer: script.answer, citations, trace: buildTrace(script, question, citations) };
}
