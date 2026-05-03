'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import { useProjectId } from '@/lib/store';
import { sendChat, ChatResponse } from '@/lib/api';
import { AlertCircle, Cpu, MessageCircle, Send, User } from 'lucide-react';

type Role = 'dev' | 'pm' | 'investor';

interface Message {
  id: string;
  from: 'user' | 'bot';
  text: string;
  mode?: string;
  confidence?: string;
  sources?: { file: string; content: string }[];
}

const ROLE_LABELS: Record<Role, string> = {
  dev:      '👨‍💻 Dev',
  pm:       '📋 PM',
  investor: '💼 Investor',
};

const SUGGESTIONS = [
  'What are the biggest security risks?',
  'Explain the main architecture',
  'What should I fix first?',
  'List all API endpoints',
];

export default function ChatPage() {
  const projectId = useProjectId();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input,    setInput]    = useState('');
  const [role,     setRole]     = useState<Role>('dev');
  const [sending,  setSending]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);
  const [mounted,  setMounted]  = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ✅ All disabled/conditional logic goes through this — safe after mount only
  const hasProject = mounted && !!projectId;

  const handleSend = async (question: string) => {
    if (!question.trim() || sending) return;

    if (!projectId) {
      setError('No project loaded. Upload a project first.');
      return;
    }

    setMessages(prev => [...prev, {
      id: `u-${Date.now()}`, from: 'user', text: question.trim(),
    }]);
    setInput('');
    setSending(true);
    setError(null);

    try {
      const res: ChatResponse = await sendChat(projectId, question.trim(), role);
      setMessages(prev => [...prev, {
        id:         `b-${Date.now()}`,
        from:       'bot',
        text:       res.answer,
        mode:       res.mode,
        confidence: res.confidence,
        sources:    res.sources,
      }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chat request failed');
    } finally {
      setSending(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleSend(input);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col bg-background">

      {/* Header */}
      <div className="border-b border-border/60 px-4 sm:px-6 py-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <MessageCircle className="size-5 text-accent" />
          <h1 className="font-bold text-base">Project Chat</h1>
          {/* ✅ Fix 1: only render after mount — projectId is undefined on server */}
          {mounted && projectId && (
            <span className="hidden sm:inline text-xs text-muted-foreground font-mono">
              ({projectId.slice(0, 8)}…)
            </span>
          )}
        </div>

        {/* Role selector */}
        <div className="flex rounded-xl overflow-hidden border border-border">
          {(Object.entries(ROLE_LABELS) as [Role, string][]).map(([r, label]) => (
            <button key={r} onClick={() => setRole(r)}
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                role === r
                  ? 'bg-accent text-white'
                  : 'bg-background text-muted-foreground hover:bg-secondary'
              }`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mx-4 mt-3 shrink-0 flex items-start gap-2 rounded-lg bg-destructive/10 border border-destructive/20 p-3">
          <AlertCircle className="size-4 text-destructive shrink-0 mt-0.5" />
          <p className="text-xs text-destructive">{error}</p>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-4">

        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-6">
            <div className="w-14 h-14 rounded-2xl bg-accent/15 flex items-center justify-center">
              <Cpu className="size-7 text-accent" />
            </div>
            <div>
              <p className="text-lg font-semibold">Ask anything about your project</p>
              {/* ✅ Fix 2: server always renders 'Loading…', client shows real state after mount */}
              <p className="text-sm text-muted-foreground mt-1">
                {mounted
                  ? hasProject
                    ? 'Project loaded — ready to chat.'
                    : 'Upload a project to begin.'
                  : 'Loading…'}
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center max-w-lg">
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => handleSend(s)}
                  // ✅ Fix 3: was `disabled={!projectId || sending}` — projectId is undefined
                  // on server → disabled=true server-side, disabled=false client-side → MISMATCH
                  // Now uses hasProject which is always false until after mount
                  disabled={!hasProject || sending}
                  className="text-xs rounded-xl border border-border bg-secondary/50 px-3 py-2 hover:bg-secondary transition-colors disabled:opacity-40">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`flex gap-3 ${msg.from === 'user' ? 'justify-end' : 'justify-start'}`}>

            {msg.from === 'bot' && (
              <div className="shrink-0 w-8 h-8 rounded-xl bg-accent/15 flex items-center justify-center mt-1">
                <Cpu className="size-4 text-accent" />
              </div>
            )}

            <div className={`max-w-[80%] flex flex-col gap-1.5 ${msg.from === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.from === 'user'
                  ? 'bg-[#635BFF] text-white rounded-tr-sm'
                  : 'bg-card border border-border rounded-tl-sm'
              }`}>
                {msg.text}
              </div>

              {msg.from === 'bot' && (
                <div className="flex gap-1.5 flex-wrap">
                  {msg.mode && (
                    <span className="text-[10px] font-mono text-muted-foreground bg-secondary px-2 py-0.5 rounded-full">
                      {msg.mode}
                    </span>
                  )}
                  {msg.confidence && (
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                      msg.confidence === 'high'
                        ? 'bg-green-500/10 text-green-400'
                        : 'bg-yellow-500/10 text-yellow-400'
                    }`}>
                      {msg.confidence} confidence
                    </span>
                  )}
                  {msg.sources && msg.sources.length > 0 && (
                    <span className="text-[10px] font-mono text-muted-foreground bg-secondary px-2 py-0.5 rounded-full">
                      {msg.sources.length} sources
                    </span>
                  )}
                </div>
              )}
            </div>

            {msg.from === 'user' && (
              <div className="shrink-0 w-8 h-8 rounded-xl bg-[#635BFF]/20 flex items-center justify-center mt-1">
                <User className="size-4 text-[#635BFF]" />
              </div>
            )}
          </div>
        ))}

        {sending && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-xl bg-accent/15 flex items-center justify-center mt-1">
              <Cpu className="size-4 text-accent animate-spin" />
            </div>
            <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1 items-center h-5">
                {[0, 1, 2].map(i => (
                  <span key={i}
                    className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit}
        className="shrink-0 border-t border-border/60 px-4 sm:px-6 py-4 flex gap-3">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          // ✅ Fix 4: placeholder depended on projectId → different server vs client text
          // ✅ Fix 5: disabled depended on projectId → disabled="" server, disabled=false client → MISMATCH
          // Both now use hasProject (always false until after mount = consistent)
          placeholder={hasProject ? `Ask as ${ROLE_LABELS[role]}…` : 'Upload a project to start chatting'}
          disabled={!hasProject || sending}
          className="flex-1 rounded-xl border border-border bg-secondary/50 px-4 py-2.5 text-sm placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-transparent disabled:opacity-50 transition-all"
        />
        <button type="submit"
          // ✅ Fix 6: was `disabled={!input.trim() || !projectId || sending}` — same issue
          disabled={!input.trim() || !hasProject || sending}
          className="shrink-0 rounded-xl bg-[#635BFF] px-4 py-2.5 text-white disabled:opacity-40 hover:bg-[#635BFF]/90 transition-colors">
          <Send className="size-4" />
        </button>
      </form>
    </div>
  );
}