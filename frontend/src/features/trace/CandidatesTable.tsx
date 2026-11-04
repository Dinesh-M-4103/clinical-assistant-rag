import type { Citation, Trace } from '@/api/schemas';
import { cn } from '@/lib/cn';
import { formatScore } from '@/lib/format';

interface CandidatesTableProps {
  candidates: Trace['candidates'];
  citations: Citation[];
}

const head = 'whitespace-nowrap px-2 py-2 text-right font-medium first:text-left';
const cell = 'px-2 py-2 text-right tabular-nums first:text-left';

/** Shows how each retrieved chunk ranked in dense search, BM25, rank fusion and the reranker. */
export function CandidatesTable({ candidates, citations }: CandidatesTableProps) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">Retrieved candidates</h3>
      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full min-w-[18rem] border-collapse text-xs">
          <caption className="sr-only">Retrieval ranks and scores per candidate chunk</caption>
          <thead className="bg-subtle text-muted">
            <tr>
              <th scope="col" className={head}>
                Chunk
              </th>
              <th scope="col" className={head}>
                Dense
              </th>
              <th scope="col" className={head}>
                BM25
              </th>
              <th scope="col" className={head}>
                Fused
              </th>
              <th scope="col" className={head}>
                Rerank
              </th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((candidate) => {
              const citation = citations.find((item) => item.id === candidate.id);
              return (
                <tr key={candidate.id} className="border-t border-border">
                  <th scope="row" className={cn(cell, 'font-medium')} title={citation?.report_name}>
                    {candidate.id}
                    {citation && (
                      <span className="font-normal text-muted"> · p.{citation.page}</span>
                    )}
                    {citation?.cited && <span className="sr-only"> (cited)</span>}
                    {citation?.cited && (
                      <span aria-hidden className="ml-1 text-primary-text">
                        ●
                      </span>
                    )}
                  </th>
                  <td className={cell}>{candidate.dense_rank ?? '—'}</td>
                  <td className={cell}>{candidate.bm25_rank ?? '—'}</td>
                  <td className={cell}>{formatScore(candidate.fused_score)}</td>
                  <td className={cell}>{formatScore(candidate.rerank_score)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted">
        <span aria-hidden className="text-primary-text">
          ●
        </span>{' '}
        cited in the answer. Ranks are 1 = best.
      </p>
    </div>
  );
}
