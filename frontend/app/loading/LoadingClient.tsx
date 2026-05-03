'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { getStatus } from '@/lib/api';
import { useProjectStore } from '@/lib/store';
import { AlertCircle, Loader } from 'lucide-react';

export function LoadingClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { projectId: storeProjectId, setProjectId } = useProjectStore();

  const projectId = useMemo(() => {
    // Priority: URL params > Zustand store > localStorage > sessionStorage
    const urlId = searchParams.get('project_id');
    if (urlId) {
      setProjectId(urlId); // Sync URL param to store
      return urlId;
    }
    return storeProjectId ||
           (typeof window !== 'undefined' ? localStorage.getItem('project_id') : null) ||
           (typeof window !== 'undefined' ? sessionStorage.getItem('project_id') : null);
  }, [searchParams, storeProjectId, setProjectId]);

  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('Initializing...');
  const [error, setError] = useState<string | null>(null);
  const [aiMode, setAiMode] = useState<'llm' | 'fallback'>('llm');

  useEffect(() => {
    if (!projectId) {
      setError('No project ID provided');
      return;
    }

    let pollInterval: ReturnType<typeof setInterval> | undefined;
    let cancelled = false;

    const poll = async () => {
      try {
        const status = await getStatus(projectId);
        if (cancelled) return;

        setProgress(status.percent);
        setCurrentStep(status.current_step_name);
        if (status.mode === 'llm' || status.mode === 'fallback') {
  setAiMode(status.mode);
} else {
  setAiMode('fallback'); // safe default
}

        const s = (status.status || '').toLowerCase();
        const isComplete = status.percent >= 100 || s === 'complete' || s === 'completed' || s === 'done' || s === 'finished';
        if (isComplete) {
          if (pollInterval) clearInterval(pollInterval);
          // Store project_id globally using Zustand (which also syncs to localStorage/sessionStorage)
          setProjectId(projectId);
          router.push(`/dashboard?project_id=${projectId}`);
        }
      } catch (err) {
        if (!cancelled) {
          setError('Failed to check project status. Please ensure the backend is running.');
        }
      }
    };

    poll();
    pollInterval = setInterval(poll, 2000);

    return () => {
      cancelled = true;
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [projectId, router]);

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-red-950 border border-red-700 rounded-lg p-6 flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h2 className="font-bold text-red-200 mb-1">Error</h2>
              <p className="text-red-300">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-cyan-600/20 rounded-full mb-4">
            <Loader className="w-8 h-8 text-cyan-400 animate-spin" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Analyzing Project</h1>
          <p className="text-slate-400">This may take a few moments...</p>
        </div>

        <div className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-8 mb-6">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-slate-300">Progress</span>
              <span className="text-sm font-bold text-cyan-400">{progress}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400 transition-all duration-300 rounded-full shadow-lg shadow-cyan-500/50"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <p className="text-xs text-slate-400 uppercase tracking-wide mb-1">Current Step</p>
            <p className="text-white font-semibold flex items-center gap-2">
              <Loader className="w-4 h-4 animate-spin text-cyan-400" />
              {currentStep}
            </p>
          </div>
        </div>

        <div className="flex items-center justify-center gap-2 text-sm text-slate-400">
          <div className={`w-2 h-2 rounded-full ${aiMode === 'llm' ? 'bg-cyan-500' : 'bg-amber-500'}`} />
          <span>{aiMode === 'llm' ? 'AI Mode' : 'Fallback Mode'}</span>
        </div>
      </div>
    </div>
  );
}

