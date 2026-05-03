'use client';

import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useProjectId } from '@/lib/store';
import {
  getAnalysis, getWorkflow, getMemory,
  AnalysisResponse, WorkflowResponse, MemoryResponse, SecurityIssue,
} from '@/lib/api';
import {
  AlertCircle, AlertTriangle, CheckCircle, ChevronDown, ChevronUp,
  Cpu, FileCode2, GitBranch, Shield, XCircle,
} from 'lucide-react';


// ─── Severity helpers ──────────────────────────────────────────────────────────


const SEV_RING: Record<string, string> = {
  CRITICAL: 'border-red-500/40 bg-red-500/10',
  HIGH:     'border-orange-500/40 bg-orange-500/10',
  MEDIUM:   'border-yellow-500/40 bg-yellow-500/10',
  LOW:      'border-blue-500/40 bg-blue-500/10',
};
const SEV_TEXT: Record<string, string> = {
  CRITICAL: 'text-red-400',
  HIGH:     'text-orange-400',
  MEDIUM:   'text-yellow-400',
  LOW:      'text-blue-400',
};
const SEV_DOT: Record<string, string> = {
  CRITICAL: 'bg-red-500',
  HIGH:     'bg-orange-500',
  MEDIUM:   'bg-yellow-500',
  LOW:      'bg-blue-500',
};


function SeverityBadge({ severity }: { severity: string }) {
  const s = severity.toUpperCase();
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold
      ${SEV_RING[s] ?? 'border-border bg-secondary'}
      ${SEV_TEXT[s] ?? 'text-muted-foreground'}`}>
      <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${SEV_DOT[s] ?? 'bg-muted-foreground'}`} />
      {s}
    </span>
  );
}


// ─── Score ring ────────────────────────────────────────────────────────────────


function ScoreRing({ score, grade }: { score: number; grade: string }) {
  const R = 38, C = 2 * Math.PI * R;
  const offset = C - (score / 100) * C;
  const color  =
    score >= 80 ? '#22c55e' :
    score >= 60 ? '#f59e0b' :
    score >= 40 ? '#f97316' : '#ef4444';


  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="100" height="100" className="-rotate-90">
        <circle cx="50" cy="50" r={R} fill="none" stroke="currentColor"
          strokeWidth="8" className="text-secondary" />
        <circle cx="50" cy="50" r={R} fill="none" stroke={color}
          strokeWidth="8" strokeDasharray={C} strokeDashoffset={offset}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <div className="absolute text-center">
        <span className="block text-xl font-bold tabular-nums" style={{ color }}>{score}</span>
        <span className="block text-xs font-bold text-muted-foreground">{grade}</span>
      </div>
    </div>
  );
}


// ─── Collapsible issue card ────────────────────────────────────────────────────


function IssueCard({ issue, idx }: { issue: SecurityIssue; idx: number }) {
  const [open, setOpen] = useState(false);
  const label = issue.type_label || issue.type?.replace(/_/g, ' ') || 'Unknown';


  return (
    <div className="rounded-xl border border-border bg-card/50 overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-secondary/40 transition-colors"
      >
        <span className="shrink-0 w-6 text-center text-xs font-mono text-muted-foreground">
          {idx + 1}
        </span>
        <SeverityBadge severity={issue.severity} />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">{label}</p>
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            {issue.file_path} · line {issue.line_number}
          </p>
        </div>
        {open
          ? <ChevronUp   className="size-4 text-muted-foreground shrink-0" />
          : <ChevronDown className="size-4 text-muted-foreground shrink-0" />
        }
      </button>


      {open && (
        <div className="border-t border-border px-4 pb-4 pt-3 space-y-3">
          {issue.explanation && (
            <p className="text-sm text-muted-foreground leading-relaxed">{issue.explanation}</p>
          )}
          {issue.code_snippet && (
            <pre className="rounded-lg bg-secondary/80 p-3 text-xs font-mono overflow-x-auto whitespace-pre-wrap break-all">
              {issue.code_snippet}
            </pre>
          )}
          {issue.fix_suggestion && (
            <div className="flex items-start gap-2 rounded-lg bg-green-500/5 border border-green-500/20 p-3">
              <CheckCircle className="size-4 text-green-500 shrink-0 mt-0.5" />
              <p className="text-xs text-green-400 leading-relaxed">{issue.fix_suggestion}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


// ─── Main Dashboard ────────────────────────────────────────────────────────────


type Tab = 'overview' | 'issues' | 'workflow' | 'memory';


export function DashboardClient() {
  const searchParams = useSearchParams();
  const urlId        = searchParams.get('project_id');
  const storeId      = useProjectId();
  const projectId    = urlId ?? storeId;


  const [mounted,  setMounted]  = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowResponse | null>(null);
  const [memory,   setMemory]   = useState<MemoryResponse   | null>(null);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);
  const [tab,      setTab]      = useState<Tab>('overview');


  useEffect(() => {
    setMounted(true);
  }, []);


  const load = useCallback(async () => {
    if (!projectId) {
      setError('No project loaded. Please upload a project first.');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const a = await getAnalysis(projectId);
      setAnalysis(a);


      const [wRes, mRes] = await Promise.allSettled([
        getWorkflow(projectId),
        getMemory(projectId),
      ]);
      if (wRes.status === 'fulfilled') setWorkflow(wRes.value);
      if (mRes.status === 'fulfilled') setMemory(mRes.value);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [projectId]);


  useEffect(() => { load(); }, [load]);


  // ── Guards ─────────────────────────────────────────────────────────────────


  if (!mounted || loading) return (
    <div className="flex h-screen items-center justify-center">
      <div className="size-8 animate-spin rounded-full border-4 border-accent border-t-transparent" />
    </div>
  );


  if (!projectId) return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <AlertCircle className="mx-auto mb-3 size-10 text-muted-foreground" />
        <p className="text-muted-foreground text-sm">No project loaded. Upload a project first.</p>
      </div>
    </div>
  );


  if (error) return (
    <div className="flex h-screen items-center justify-center p-8">
      <div className="max-w-sm text-center">
        <XCircle className="mx-auto mb-3 size-10 text-destructive" />
        <p className="text-sm text-muted-foreground mb-4">{error}</p>
        <button
          onClick={load}
          className="rounded-xl bg-[#635BFF] px-6 py-2.5 text-sm font-semibold text-white hover:bg-[#635BFF]/90 transition-colors"
        >
          Retry
        </button>
      </div>
    </div>
  );


  if (!analysis) return null;


  const {
    summary, issues, total_issues,
    critical_count, high_count, medium_count, low_count,
    security_score, grade,
  } = analysis;


  // workflow can come from standalone route OR embedded in analysis
  const wf = workflow?.workflow ?? analysis.workflow;


  const TABS: { id: Tab; label: string }[] = [
    { id: 'overview',  label: 'Overview' },
    { id: 'issues',    label: `Issues (${total_issues})` },
    { id: 'workflow',  label: 'Workflow' },
    { id: 'memory',    label: 'Memory' },
  ];


  return (
    <div className="min-h-screen bg-background">


      {/* ── Sticky header ───────────────────────────────────────────────── */}
      <div className="sticky top-0 z-10 border-b border-border/60 bg-background/80 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold truncate">{analysis.project_name}</h1>
            <p className="text-xs text-muted-foreground">
              {analysis.total_files_analyzed} files · {summary.project_type || 'Unknown type'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Shield className={`size-5 ${
              security_score >= 70 ? 'text-green-500' :
              security_score >= 50 ? 'text-yellow-500' : 'text-red-500'
            }`} />
            <span className="text-sm font-bold tabular-nums">{security_score}/100</span>
            <span className="text-xs text-muted-foreground font-mono">({grade})</span>
          </div>
        </div>


        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex gap-1 overflow-x-auto">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`whitespace-nowrap px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === t.id
                  ? 'border-accent text-accent'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}>
              {t.label}
            </button>
          ))}
        </div>
      </div>


      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">


        {/* ── Overview ──────────────────────────────────────────────────── */}
        {tab === 'overview' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">


            <div className="rounded-2xl border border-border bg-card p-6 flex flex-col items-center justify-center gap-3">
              <ScoreRing score={security_score} grade={grade} />
              <p className="text-sm text-muted-foreground font-medium">Security Score</p>
            </div>


            <div className="rounded-2xl border border-border bg-card p-6">
              <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                Issue Breakdown
              </h3>
              <div className="space-y-3">
                {([
                  ['CRITICAL', critical_count, 'bg-red-500'],
                  ['HIGH',     high_count,     'bg-orange-500'],
                  ['MEDIUM',   medium_count,   'bg-yellow-500'],
                  ['LOW',      low_count,      'bg-blue-500'],
                ] as [string, number, string][]).map(([label, count, dot]) => (
                  <div key={label} className="flex items-center gap-3">
                    <span className={`h-2 w-2 rounded-full shrink-0 ${dot}`} />
                    <span className="flex-1 text-sm">{label}</span>
                    <span className="text-sm font-bold tabular-nums">{count}</span>
                  </div>
                ))}
              </div>
            </div>


            <div className="rounded-2xl border border-border bg-card p-6">
              <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                Tech Stack
              </h3>
              {summary.tech_stack?.length ? (
                <div className="flex flex-wrap gap-2">
                  {summary.tech_stack.map(t => (
                    <span key={t} className="rounded-lg bg-secondary px-3 py-1 text-xs font-medium">{t}</span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">Not detected</p>
              )}
            </div>


            <div className="sm:col-span-2 lg:col-span-3 rounded-2xl border border-border bg-card p-6">
              <h3 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                <FileCode2 className="size-4" /> Project Description
              </h3>
              <p className="text-sm leading-relaxed">{summary.description || 'No description available.'}</p>
              {summary.entry_point && !['Unknown', 'unknown'].includes(summary.entry_point) && (
                <p className="mt-3 text-xs text-muted-foreground">
                  Entry point:{' '}
                  <code className="font-mono bg-secondary px-1.5 py-0.5 rounded">{summary.entry_point}</code>
                </p>
              )}
              {summary.architecture_type && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Architecture:{' '}
                  <span className="text-foreground font-medium">{summary.architecture_type}</span>
                </p>
              )}
            </div>
          </div>
        )}


        {/* ── Issues ────────────────────────────────────────────────────── */}
        {tab === 'issues' && (
          <div className="space-y-3">
            {issues.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <CheckCircle className="mb-3 size-12 text-green-500" />
                <h3 className="text-lg font-semibold">No Issues Found</h3>
                <p className="mt-1 text-sm text-muted-foreground">Your codebase looks clean!</p>
              </div>
            ) : (
              issues.map((issue, i) => (
                <IssueCard
                  key={`${issue.file_path}:${issue.line_number}:${i}`}
                  issue={issue}
                  idx={i}
                />
              ))
            )}
          </div>
        )}


        {/* ── Workflow ──────────────────────────────────────────────────── */}
        {tab === 'workflow' && (
          <div className="space-y-5">
            {wf ? (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {([
                    ['Stage',      wf.stage      || wf.stage_label || '—'],
                    ['Risk Level', wf.risk        || wf.risk_level  || '—'],
                    ['Grade',      wf.grade                         || '—'],
                  ] as [string, string][]).map(([label, value]) => (
                    <div key={label} className="rounded-2xl border border-border bg-card p-5 text-center">
                      <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wider">{label}</p>
                      <p className="text-2xl font-bold">{value}</p>
                    </div>
                  ))}
                </div>


                {wf.recommended_action && (
                  <div className="rounded-2xl border border-border bg-card p-6">
                    <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">
                      Recommended Action
                    </h3>
                    <p className="text-sm">{wf.recommended_action}</p>
                  </div>
                )}


                {wf.blockers?.length > 0 && (
                  <div className="rounded-2xl border border-border bg-card p-6">
                    <h3 className="mb-3 flex items-center gap-2 font-semibold text-sm">
                      <AlertTriangle className="size-4 text-orange-500" /> Blockers
                    </h3>
                    <ul className="space-y-2">
                      {wf.blockers.map((b, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-orange-500" />
                          {b}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <p className="text-center text-muted-foreground py-12 text-sm">
                Workflow data not yet available.
              </p>
            )}
          </div>
        )}


        {/* ── Memory ────────────────────────────────────────────────────── */}
        {tab === 'memory' && (() => {
          const mem = memory ?? {
            recent_work: analysis.memory?.recent_work ?? [],
            features:    [],
            security:    [],
            refactors:   [],
          };


          return (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {([
                ['Recent Work', mem.recent_work, GitBranch],
                ['Features',   mem.features,    FileCode2],
                ['Security',   mem.security,    Shield],
                ['Refactors',  mem.refactors,   Cpu],
              ] as [string, string[], React.ElementType][]).map(([label, items, Icon]) => (
                <div key={label} className="rounded-2xl border border-border bg-card p-6">
                  <h3 className="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                    <Icon className="size-4" /> {label}
                  </h3>
                  {items?.length ? (
                    <ul className="space-y-2">
                      {items.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-muted-foreground">No data recorded.</p>
                  )}
                </div>
              ))}
            </div>
          );
        })()}
      </div>
    </div>
  );
}