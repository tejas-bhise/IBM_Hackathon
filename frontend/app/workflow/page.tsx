import { Suspense } from 'react';
import { WorkflowClient } from './WorkflowClient';

export const dynamic = 'force-dynamic';

export default function WorkflowPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 flex items-center justify-center">
          <p className="text-slate-300">Loading workflow…</p>
        </div>
      }
    >
      <WorkflowClient />
    </Suspense>
  );
}

