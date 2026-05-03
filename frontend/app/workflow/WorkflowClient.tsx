'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { getWorkflow, type WorkflowData } from '@/lib/api';
import { AlertCircle, Loader, ShieldAlert, Target, Workflow } from 'lucide-react';

type Tab = 'dev' | 'pm' | 'investor';

function riskLabel(risk: number) {
  if (risk >= 80) return { label: 'High', cls: 'bg-red-600 text-white' };
  if (risk >= 50) return { label: 'Medium', cls: 'bg-yellow-600 text-white' };
  return { label: 'Low', cls: 'bg-green-600 text-white' };
}

export function WorkflowClient() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const projectId = useMemo(() => {
    return searchParams.get('project_id') || (typeof window !== 'undefined' ? sessionStorage.getItem('project_id') : null);
  }, [searchParams]);

  const [tab, setTab] = useState<Tab>('dev');
  const [data, setData] = useState<WorkflowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) {
      setError('No project ID found. Please upload a project first.');
      setLoading(false);
      return;
    }

    let cancelled = false;
    const run = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await getWorkflow(projectId);
        if (!cancelled) setData(res.workflow);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load workflow.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    run();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  if (!projectId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-950 border border-red-700 rounded-lg p-6 flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h2 className="font-bold text-red-200 mb-1">Missing project ID</h2>
              <p className="text-red-300">Upload a project to view workflow insights.</p>
              <button
                onClick={() => router.push('/upload')}
                className="mt-4 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-medium transition"
              >
                Go to Upload
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800">
      <div className="border-b border-slate-700 bg-slate-950/50 backdrop-blur sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-1 flex items-center gap-2">
              <Workflow className="w-7 h-7 text-cyan-400" />
              Workflow
            </h1>
            <p className="text-slate-400 text-sm">
              Project ID: <span className="font-mono text-slate-300">{projectId}</span>
            </p>
          </div>
          <button
            onClick={() => router.push(`/dashboard?project_id=${projectId}`)}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="inline-flex rounded-lg border border-slate-700 bg-slate-900/40 p-1 mb-6">
          {(['dev', 'pm', 'investor'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition ${
                tab === t ? 'bg-cyan-600 text-white' : 'text-slate-300 hover:text-white'
              }`}
            >
              {t === 'dev' ? 'Dev view' : t === 'pm' ? 'PM view' : 'Investor view'}
            </button>
          ))}
        </div>

        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <Loader className="w-12 h-12 text-cyan-400 animate-spin mx-auto mb-4" />
              <p className="text-slate-300">Loading workflow...</p>
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="bg-red-950 border border-red-700 rounded-lg p-6 flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h2 className="font-bold text-red-200 mb-1">Failed to load workflow</h2>
              <p className="text-red-300">{error}</p>
              <button
                onClick={() => router.refresh()}
                className="mt-4 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {!loading && !error && data && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-6">
              <p className="text-sm text-slate-400 uppercase tracking-wide mb-2">Stage</p>
              <div className="flex items-center justify-between gap-4">
                <h2 className="text-2xl font-bold text-white">{data.stage}</h2>
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-slate-300" />
                  <span className={`text-xs font-bold px-3 py-1 rounded ${riskLabel(Number(data.risk)).cls}`}>
                    Risk: {riskLabel(Number(data.risk)).label} ({data.risk})
                  </span>
                </div>
              </div>

              <div className="mt-6 bg-slate-900/40 border border-slate-700 rounded-lg p-4">
                <p className="text-sm text-slate-400 uppercase tracking-wide mb-2">Recommended action</p>
                <p className="text-slate-100 whitespace-pre-wrap">{data.recommended_action}</p>
              </div>

              <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-slate-900/40 border border-slate-700 rounded-lg p-4">
                  <p className="text-xs text-slate-400 uppercase tracking-wide mb-2">Security score</p>
                  <p className="text-2xl font-bold text-white">{data.metrics?.security_score ?? '—'}</p>
                </div>
                <div className="bg-slate-900/40 border border-slate-700 rounded-lg p-4">
                  <p className="text-xs text-slate-400 uppercase tracking-wide mb-2">Code quality</p>
                  <p className="text-2xl font-bold text-white">{data.metrics?.code_quality ?? '—'}</p>
                </div>
                <div className="bg-slate-900/40 border border-slate-700 rounded-lg p-4">
                  <p className="text-xs text-slate-400 uppercase tracking-wide mb-2">Test coverage</p>
                  <p className="text-2xl font-bold text-white">{data.metrics?.test_coverage ?? '—'}</p>
                </div>
              </div>
            </div>

            <div className="bg-slate-900/40 border border-slate-700 rounded-lg p-6">
              <p className="text-sm text-slate-400 uppercase tracking-wide mb-4">View guidance</p>

              {tab === 'dev' && (
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <Target className="w-5 h-5 text-cyan-300 mt-0.5" />
                    <p className="text-slate-200 text-sm">
                      Focus on actionable engineering steps: fix high-risk findings first, then harden CI checks.
                    </p>
                  </div>
                  <button
                    onClick={() => router.push(`/chat?project_id=${projectId}`)}
                    className="w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-semibold transition"
                  >
                    Ask in Chat (Dev)
                  </button>
                </div>
              )}

              {tab === 'pm' && (
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <Target className="w-5 h-5 text-cyan-300 mt-0.5" />
                    <p className="text-slate-200 text-sm">
                      Translate risk into milestones: assign owners, create a short remediation sprint, and track regression.
                    </p>
                  </div>
                  <button
                    onClick={() => router.push(`/chat?project_id=${projectId}`)}
                    className="w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-semibold transition"
                  >
                    Ask in Chat (PM)
                  </button>
                </div>
              )}

              {tab === 'investor' && (
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <Target className="w-5 h-5 text-cyan-300 mt-0.5" />
                    <p className="text-slate-200 text-sm">
                      Consider delivery risk and timeline: use stage and risk to assess execution predictability and security posture.
                    </p>
                  </div>
                  <button
                    onClick={() => router.push(`/chat?project_id=${projectId}`)}
                    className="w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-semibold transition"
                  >
                    Ask in Chat (Investor)
                  </button>
                </div>
              )}

              <div className="mt-6 border-t border-slate-700 pt-4">
                <p className="text-xs text-slate-500">
                  Note: “Fallback Mode” is not an error. Use chat to get tailored guidance for each audience.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

