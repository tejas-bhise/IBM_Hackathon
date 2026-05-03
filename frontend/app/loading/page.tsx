'use client';

import { useEffect, useRef, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useProjectStore } from '@/lib/store';
import { getStatus, StatusResponse } from '@/lib/api';
import { AlertCircle, CheckCircle, Cpu } from 'lucide-react';

const POLL_MS = 2500;

const STEP_LABELS = [
  'Ingesting repository',
  'Extracting files',
  'Scanning code',
  'Building embeddings',
  'Running AI analysis',
  'Generating workflow',
  'Building memory',
  'Generating mock data',
  'Finalising report',
];

function LoadingContent() {
  const router             = useRouter();
  const params             = useSearchParams();
  const { setProjectId }   = useProjectStore();
  const urlProjectId       = params.get('project_id');

  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error,  setError]  = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!urlProjectId) {
      setError('No project ID in URL. Please upload a project first.');
      return;
    }

    setProjectId(urlProjectId);

    const poll = async () => {
      try {
        const data = await getStatus(urlProjectId);
        setStatus(data);

        if (data.status === 'completed') {
          if (timerRef.current) clearInterval(timerRef.current);
          router.push(`/dashboard?project_id=${urlProjectId}`);
          return;
        }

        if (data.status === 'error') {
          if (timerRef.current) clearInterval(timerRef.current);
          setError(data.error ?? 'Analysis failed. Please try again.');
        }
      } catch (err) {
        console.warn('[Loading] Poll failed:', err);
      }
    };

    poll();
    timerRef.current = setInterval(poll, POLL_MS);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [urlProjectId, router, setProjectId]);

  const percent  = status?.percent          ?? 0;
  const stepName = status?.current_step_name ?? 'Starting…';
  const step     = status?.pipeline_step     ?? 0;
  const total    = status?.total_steps       ?? STEP_LABELS.length;

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-8">
        <div className="max-w-sm w-full text-center">
          <AlertCircle className="mx-auto mb-4 size-12 text-destructive" />
          <h2 className="text-xl font-bold mb-2">Analysis Failed</h2>
          <p className="text-sm text-muted-foreground mb-6">{error}</p>
          <button
            onClick={() => router.push('/dashboard/upload')}
            className="rounded-xl bg-[#635BFF] px-6 py-2.5 text-sm font-semibold text-white hover:bg-[#635BFF]/90 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-8">
      <div className="w-full max-w-md text-center">
        <div className="relative mx-auto mb-8 w-20 h-20">
          <div className="absolute inset-0 rounded-2xl bg-accent/20 blur-xl animate-pulse" />
          <div className="relative w-20 h-20 rounded-2xl bg-background border border-border flex items-center justify-center shadow-lg">
            <Cpu className="size-10 text-accent animate-spin" style={{ animationDuration: '2s' }} />
          </div>
        </div>

        <h2 className="text-2xl font-bold mb-1">Analysing your project…</h2>
        <p className="text-sm text-muted-foreground mb-8">{stepName}</p>

        <div className="w-full bg-secondary rounded-full h-2 overflow-hidden mb-3">
          <div
            className="bg-accent h-full rounded-full transition-all duration-700 ease-out"
            style={{ width: `${percent}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-muted-foreground font-mono mb-8">
          <span>Step {step}/{total}</span>
          <span>{percent}%</span>
        </div>

        <div className="flex justify-center gap-1.5 flex-wrap">
          {STEP_LABELS.map((label, i) => {
            const done    = i < step;
            const current = i === step;
            return (
              <div
                key={label}
                title={label}
                className={`h-2 w-2 rounded-full transition-colors duration-300 ${
                  done    ? 'bg-accent' :
                  current ? 'bg-accent/50 animate-pulse' :
                            'bg-secondary'
                }`}
              />
            );
          })}
        </div>

        {status?.status === 'completed' && (
          <div className="mt-6 flex items-center justify-center gap-2 text-sm text-green-500">
            <CheckCircle className="size-4" />
            Complete! Redirecting…
          </div>
        )}
      </div>
    </div>
  );
}

export default function LoadingPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Cpu className="size-8 animate-spin text-accent" />
      </div>
    }>
      <LoadingContent />
    </Suspense>
  );
}