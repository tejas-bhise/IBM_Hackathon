'use client';


import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { sendChat, type ChatResponse } from '@/lib/api';
import { useProjectStore } from '@/lib/store';
import { AlertCircle, Loader, Send, AlertTriangle, FileCode } from 'lucide-react';


type Role = 'dev' | 'pm' | 'investor';


type ChatMessage =
  | { id: string; kind: 'user'; text: string; createdAt: number }
  | { id: string; kind: 'assistant'; text: string; payload: ChatResponse; createdAt: number };


function confidenceClass(confidence: number | undefined) {
  if (confidence === undefined || isNaN(confidence)) {
    return 'text-slate-300 bg-slate-950/30 border-slate-700/40';
  }
  if (confidence >= 0.8) return 'text-green-300 bg-green-950/30 border-green-700/40';
  if (confidence >= 0.5) return 'text-yellow-200 bg-yellow-950/30 border-yellow-700/40';
  return 'text-red-200 bg-red-950/30 border-red-700/40';
}


function confidenceLabel(confidence: number | undefined): string {
  if (confidence === undefined || isNaN(confidence)) {
    return 'Low confidence';
  }
  return `${(confidence * 100).toFixed(0)}%`;
}


// Filter out docs/ paths from sources
function filterSources(sources: unknown[]): unknown[] {
  if (!Array.isArray(sources)) return [];
  return sources.filter(s => {
    if (typeof s === 'string') {
      return !s.includes('docs/');
    }
    if (typeof s === 'object' && s !== null && 'file' in s) {
      return !(s as Record<string, unknown>).file?.toString().includes('docs/');
    }
    return true;
  });
}


export function ChatClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { projectId: storeProjectId, setProjectId: setStoreProjectId } = useProjectStore();


  // 1. FIX HYDRATION: Start with null and only set after mounting
  const [mounted, setMounted] = useState(false);
  const [projectId, setProjectId] = useState<string | null>(null);


  useEffect(() => {
    setMounted(true);
    // Priority: URL params > Zustand store > localStorage > sessionStorage
    const urlId = searchParams.get('project_id');
    if (urlId) {
      setStoreProjectId(urlId); // Sync URL param to store
      setProjectId(urlId);
    } else {
      const id = storeProjectId ||
                 localStorage.getItem('project_id') ||
                 sessionStorage.getItem('project_id');
      setProjectId(id);
    }
  }, [searchParams, storeProjectId, setStoreProjectId]);


  const [role, setRole] = useState<Role>('dev');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);


  const bottomRef = useRef<HTMLDivElement | null>(null);


  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, loading]);


  // Debounced submit to avoid duplicate calls
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const onSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Prevent duplicate submissions
    if (isSubmitting || loading) return;
    
    if (!projectId) {
      setError('No project ID found.');
      return;
    }
    const q = question.trim();
    if (!q) return;


    setError(null);
    setLoading(true);
    setIsSubmitting(true);
    setQuestion('');


    const userMsg: ChatMessage = { id: crypto.randomUUID(), kind: 'user', text: q, createdAt: Date.now() };
    setMessages((prev) => [...prev, userMsg]);


    try {
      // Send only last 3 messages for context (token optimization)
      const recentMessages = messages.slice(-3);
      const res = await sendChat(projectId, q, role);
      
      // Validate response
      if (!res || !res.answer) {
        throw new Error('Invalid response from server');
      }
      
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        kind: 'assistant',
        text: res.answer,
        payload: res,
        createdAt: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send chat message.');
      // Remove the user message if request failed
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
      setIsSubmitting(false);
    }
  }, [projectId, question, role, messages, loading, isSubmitting]);


  // Prevent hydration mismatch by returning null until client-side state is ready
  if (!mounted) return null;


  if (!projectId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 p-6">
        <div className="max-w-3xl mx-auto">
          <div className="bg-red-950 border border-red-700 rounded-lg p-6 flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h2 className="font-bold text-red-200 mb-1">Missing project ID</h2>
              <p className="text-red-300">Go to upload and analyze a project first.</p>
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
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">Chat</h1>
            <p className="text-slate-400 text-sm">
              Project ID: <span className="font-mono text-slate-300">{projectId}</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
              className="bg-slate-900 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
              disabled={loading}
            >
              <option value="dev">Dev view</option>
              <option value="pm">PM view</option>
              <option value="investor">Investor view</option>
            </select>
            <button
              onClick={() => router.push(`/dashboard?project_id=${projectId}`)}
              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition"
            >
              Dashboard
            </button>
          </div>
        </div>
      </div>


      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="mb-4 bg-red-950 border border-red-700 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}


        <div className="bg-slate-900/40 border border-slate-700 rounded-lg overflow-hidden">
          <div className="p-4 sm:p-6 space-y-4 max-h-[65vh] overflow-y-auto">
            {messages.map((m) => {
              if (m.kind === 'user') {
                return (
                  <div key={m.id} className="flex justify-end">
                    <div className="max-w-[85%] bg-cyan-600/20 border border-cyan-600/40 rounded-lg px-4 py-3">
                      <p className="text-cyan-50 whitespace-pre-wrap">{m.text}</p>
                    </div>
                  </div>
                );
              }


              const conf = typeof m.payload.confidence === 'number' ? m.payload.confidence : undefined;
              const isFallback = m.payload.mode === 'fallback';
              const isAiMode = m.payload.mode === 'gemini' || m.payload.mode === 'groq';
              const filteredSources = filterSources(m.payload.sources || []);
              
              return (
                <div key={m.id} className="flex justify-start">
                  <div className="max-w-[85%] bg-slate-800/70 border border-slate-700 rounded-lg px-4 py-3">
                    {/* Fallback Mode Banner */}
                    {isFallback && (
                      <div className="mb-3 bg-amber-950/30 border border-amber-700/40 rounded-lg p-3 flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                        <div className="text-xs text-amber-200">
                          <strong>AI unavailable</strong> — showing code-based analysis
                        </div>
                      </div>
                    )}
                    
                    <div className="flex flex-wrap items-center gap-2 mb-3">
                      <span className={`text-xs font-semibold px-2 py-1 rounded border ${
                        isAiMode
                          ? 'text-cyan-200 bg-cyan-950/30 border-cyan-700/40'
                          : 'text-amber-200 bg-amber-950/30 border-amber-700/40'
                      }`}>
                        {isAiMode ? 'AI Mode' : 'Deterministic Mode'}
                      </span>
                      <span className={`text-xs font-semibold px-2 py-1 rounded border ${confidenceClass(conf)}`}>
                        Confidence: {confidenceLabel(conf)}
                      </span>
                    </div>


                    {/* Answer - structured for fallback */}
                    {isFallback ? (
                      <div className="text-slate-100 space-y-2">
                        {m.payload.answer.split('\n').map((line, i) => (
                          <div key={i} className="whitespace-pre-wrap">
                            {line.startsWith('File:') || line.startsWith('Function:') || line.startsWith('Logic:') ? (
                              <div className="font-semibold text-amber-200">{line}</div>
                            ) : (
                              <div>{line}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-slate-100 whitespace-pre-wrap">{m.payload.answer}</p>
                    )}


                    <div className="mt-4 grid grid-cols-1 gap-3">
                      {/* Reasoning Section */}
                      {m.payload.reasoning && Array.isArray(m.payload.reasoning) && m.payload.reasoning.length > 0 && (
                        <div className="bg-slate-900/40 border border-slate-700 rounded-lg p-3">
                          <p className="text-xs text-slate-400 uppercase tracking-wide mb-2">Reasoning</p>
                          <div className="space-y-1 text-sm text-slate-200">
                            {m.payload.reasoning.map((r: unknown, i: number) => (
                              <div key={i} className="flex items-start gap-2">
                                <FileCode className="w-3 h-3 text-slate-400 mt-1 flex-shrink-0" />
                                <span>
                                  {typeof r === 'object' && r !== null && 'file' in r
                                    ? `${(r as Record<string, unknown>).file} (Lines ${(r as Record<string, unknown>).start_line}-${(r as Record<string, unknown>).end_line})`
                                    : typeof r === 'string' ? r : JSON.stringify(r)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}


                      {/* Sources Section - Filtered */}
                      {filteredSources.length > 0 && (
                        <div className="bg-slate-900/40 border border-slate-700 rounded-lg p-3">
                          <p className="text-xs text-slate-400 uppercase tracking-wide mb-2">Sources</p>
                          <ul className="space-y-1 text-sm">
                            {filteredSources.map((s: unknown, idx: number) => (
                              <li key={idx} className="flex items-start gap-2">
                                <FileCode className="w-3 h-3 text-slate-400 mt-1 flex-shrink-0" />
                                {typeof s === 'string' ? (
                                  <span className="text-cyan-300 font-mono text-xs break-all">{s}</span>
                                ) : (
                                  <span className="text-slate-300 font-mono text-xs">
                                    {(s as Record<string, unknown>).file as string} (Lines {(s as Record<string, unknown>).start_line as number}-{(s as Record<string, unknown>).end_line as number})
                                  </span>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-800/70 border border-slate-700 rounded-lg px-4 py-3 flex items-center gap-2 text-slate-200">
                  <Loader className="w-4 h-4 animate-spin text-cyan-400" /> Thinking...
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>


          <form onSubmit={onSubmit} className="border-t border-slate-700 p-3 sm:p-4 bg-slate-950/40">
            <div className="flex items-center gap-3">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question…"
                className="flex-1 bg-slate-900 border border-slate-700 text-slate-100 rounded-lg px-4 py-3 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || isSubmitting || !question.trim()}
                className="px-4 py-3 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition inline-flex items-center gap-2"
              >
                {loading || isSubmitting ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" /> Sending...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" /> Send
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}