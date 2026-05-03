'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  Send,
  Loader,
  Sparkles,
  BookOpen,
  Clock,
  Shield,
  Paperclip,
  Link2,
  FileArchive,
  ImageIcon,
  FileText,
  X,
  FolderGit2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export type ChatAttachment = {
  id: string;
  kind: 'file' | 'repo';
  label: string;
  sizeBytes?: number;
};

const FILE_ACCEPT =
  'image/*,.pdf,.zip,application/pdf,application/zip,application/x-zip-compressed';

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function isLikelyRepoUrl(s: string): boolean {
  try {
    const u = new URL(s.trim());
    return u.protocol === 'http:' || u.protocol === 'https:';
  } catch {
    return false;
  }
}

export function AIChat() {
  const reduceMotion = useReducedMotion();

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      type: 'assistant',
      content:
        "Hello! I'm your AI Project Intelligence Assistant. I can help you understand your codebase, identify vulnerabilities, and answer questions about your project. Tap the paperclip to add images, PDFs, ZIP archives, or a repository link, then send your message.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
  const [repoUrlInput, setRepoUrlInput] = useState('');
  const [attachOpen, setAttachOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const quickQuestions = [
    {
      icon: BookOpen,
      label: 'Code Structure',
      question: 'Where is authentication handled in this project?',
    },
    {
      icon: Clock,
      label: 'Recent Changes',
      question: 'What changed recently in the codebase?',
    },
    {
      icon: Shield,
      label: 'Security Issues',
      question: 'What are the most critical security issues?',
    },
  ];

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const handleFilesSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const list = e.target.files;
    if (!list?.length) return;
    const next: ChatAttachment[] = [];
    for (let i = 0; i < list.length; i++) {
      const file = list[i];
      next.push({
        id: `file-${Date.now()}-${i}-${file.name}`,
        kind: 'file',
        label: file.name,
        sizeBytes: file.size,
      });
    }
    setAttachments((prev) => [...prev, ...next]);
    e.target.value = '';
    setAttachOpen(false);
  };

  const addRepoUrl = () => {
    const trimmed = repoUrlInput.trim();
    if (!trimmed || !isLikelyRepoUrl(trimmed)) return;
    setAttachments((prev) => [
      ...prev,
      {
        id: `repo-${Date.now()}`,
        kind: 'repo',
        label: trimmed,
      },
    ]);
    setRepoUrlInput('');
    setAttachOpen(false);
  };

  const buildUserContent = (messageText: string, att: ChatAttachment[]): string => {
    const parts: string[] = [];
    if (att.length) {
      const lines = att.map((a) => {
        if (a.kind === 'file') {
          const sz = a.sizeBytes != null ? ` (${formatBytes(a.sizeBytes)})` : '';
          return `- File: ${a.label}${sz}`;
        }
        return `- Repository: ${a.label}`;
      });
      parts.push('Attached sources\n' + lines.join('\n'));
    }
    if (messageText.trim()) parts.push(messageText.trim());
    return parts.join('\n\n');
  };

  const generateMockResponse = (userMessage: string, att: ChatAttachment[]): string => {
    if (att.length) {
      const fileCount = att.filter((a) => a.kind === 'file').length;
      const repoCount = att.filter((a) => a.kind === 'repo').length;
      return `I've registered your sources for analysis:

**Summary**
${fileCount ? `- ${fileCount} file(s) (images, PDF, or ZIP)` : ''}${fileCount && repoCount ? '\n' : ''}${repoCount ? `- ${repoCount} repository link(s)` : ''}

When your backend is connected, these will be ingested for security scanning and project understanding. For now this is a demo: files stay in your browser only and are not uploaded to a server.

You can ask follow-up questions about what you attached or about your project in general.`;
    }

    const lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.includes('authentication') || lowerMessage.includes('auth')) {
      return `Based on my analysis of your project, authentication is primarily handled in the following areas:

1. **Auth Routes**: Located in \`/app/api/auth\` with OAuth2 implementation
2. **Session Management**: Handled by the middleware in \`/middleware.ts\` using JWT tokens
3. **User Context**: Global state management in \`/lib/auth-context.tsx\`
4. **Protected Routes**: Route guards implemented in \`/app/dashboard/layout.tsx\`

The authentication flow uses secure HTTP-only cookies and implements proper CSRF protection. All sensitive credentials are stored in environment variables.`;
    } else if (
      lowerMessage.includes('recent') ||
      lowerMessage.includes('changed') ||
      lowerMessage.includes('update')
    ) {
      return `Here are the most recent changes to your project:

**Last 5 changes:**
1. ✅ Added Payment Integration (3 days ago)
2. 🔒 Fixed Security Vulnerability in SQL queries (1 week ago)
3. 🎨 Updated UI components styling (1 week ago)
4. 🐛 Fixed authentication middleware bug (2 weeks ago)
5. 📦 Updated dependencies to latest versions (3 weeks ago)

The most significant recent work was integrating Stripe for payment processing and implementing parameterized queries to prevent SQL injection attacks.`;
    } else if (
      lowerMessage.includes('security') ||
      lowerMessage.includes('vulnerability') ||
      lowerMessage.includes('vulnerability')
    ) {
      return `Security Analysis Summary:

**Critical Issues (1):**
- Potential SQL Injection in user search (database.ts:234)

**Medium Issues (3):**
- Hardcoded API keys in environment config
- Missing rate limiting on login endpoint
- Unvalidated file uploads

**Low Issues (2):**
- XSS vulnerability in comment rendering
- Missing HTTPS redirect

Recommended actions:
1. Implement parameterized queries immediately
2. Move secrets to proper env var management
3. Add rate limiting middleware
4. Validate all file uploads server-side`;
    } else if (lowerMessage.includes('explain') || lowerMessage.includes('how')) {
      return `I can help explain different aspects of your project:

**Available explanations:**
- Project architecture and module structure
- Authentication and authorization flow
- Database schema and relationships
- API endpoints and integrations
- Security configurations
- Deployment process

Could you be more specific about what you'd like me to explain?`;
    } else {
      return `I've analyzed your project and here's what I found:

Your application is a modern full-stack web application with:
- **Frontend**: React with TypeScript and Tailwind CSS
- **Backend**: Node.js with Express API routes
- **Database**: PostgreSQL with Prisma ORM
- **Authentication**: JWT-based with secure session management

Key strengths:
✅ Well-structured codebase with clear separation of concerns
✅ Strong security practices with parameterized queries
✅ Comprehensive error handling throughout

Areas for improvement:
⚠️ Add more comprehensive unit tests
⚠️ Implement caching strategy for performance
⚠️ Add API rate limiting

Feel free to ask specific questions about your codebase!`;
    }
  };

  const handleSendMessage = async (messageText: string) => {
    const trimmed = messageText.trim();
    if (!trimmed && attachments.length === 0) return;

    const content = buildUserContent(trimmed, attachments);
    const snapshot = [...attachments];

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setAttachments([]);
    setIsLoading(true);

    setTimeout(() => {
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: generateMockResponse(trimmed, snapshot),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 800);
  };

  const handleSend = () => {
    handleSendMessage(input);
  };

  const handleQuickQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const fileIcon = (name: string) => {
    const lower = name.toLowerCase();
    if (/\.(png|jpe?g|gif|webp|svg|bmp|ico)$/i.test(lower))
      return <ImageIcon className="size-3.5 shrink-0 text-muted-foreground" />;
    if (/\.pdf$/i.test(lower)) return <FileText className="size-3.5 shrink-0 text-muted-foreground" />;
    if (/\.zip$/i.test(lower)) return <FileArchive className="size-3.5 shrink-0 text-muted-foreground" />;
    return <FileText className="size-3.5 shrink-0 text-muted-foreground" />;
  };

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reduceMotion ? 0 : 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="relative flex flex-col h-full rounded-xl overflow-hidden min-h-[520px] border border-border/80 bg-secondary/90 backdrop-blur-sm shadow-[0_0_44px_-14px_oklch(0.55_0.19_262.95_/_0.45)] ring-1 ring-accent/20"
    >
      <div className="pointer-events-none absolute inset-0 rounded-xl opacity-40 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,oklch(0.55_0.19_262.95_/_0.2),transparent)] motion-reduce:opacity-0" />
      {/* Header */}
      <div className="relative border-b border-border/80 p-6 bg-background/40 backdrop-blur-md">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-lg bg-accent/20 ring-1 ring-accent/30 flex items-center justify-center shadow-inner shadow-accent/10">
            <Sparkles size={20} className="text-accent" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">AI Project Assistant</h2>
            <p className="text-xs text-muted-foreground">Powered by project intelligence</p>
          </div>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn('flex', message.type === 'user' ? 'justify-end' : 'justify-start')}
          >
            <div
              className={cn(
                'max-w-xl px-4 py-3 rounded-lg',
                message.type === 'user'
                  ? 'bg-accent text-accent-foreground rounded-br-none'
                  : 'bg-background border border-border text-foreground rounded-bl-none'
              )}
            >
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
              <p
                className={cn(
                  'text-xs mt-2',
                  message.type === 'user' ? 'text-accent-foreground/70' : 'text-muted-foreground'
                )}
              >
                {message.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-background border border-border text-foreground px-4 py-3 rounded-lg rounded-bl-none">
              <div className="flex items-center gap-2">
                <Loader size={16} className="animate-spin text-accent" />
                <p className="text-sm">Analyzing your project...</p>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick questions */}
      {messages.length <= 1 && !isLoading && (
        <div className="px-6 pb-4">
          <p className="text-xs font-semibold text-muted-foreground mb-3 uppercase">Quick Questions</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {quickQuestions.map((q) => {
              const Icon = q.icon;
              return (
                <button
                  key={q.question}
                  onClick={() => handleQuickQuestion(q.question)}
                  className="text-left px-4 py-3 rounded-lg border border-border bg-background/50 hover:bg-background hover:border-accent/50 transition-all group"
                >
                  <div className="flex items-start gap-3">
                    <Icon
                      size={16}
                      className="text-muted-foreground group-hover:text-accent mt-0.5 shrink-0"
                    />
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-foreground">{q.label}</p>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{q.question}</p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-border p-6 bg-background/50">
        <input
          ref={fileInputRef}
          type="file"
          className="sr-only"
          accept={FILE_ACCEPT}
          multiple
          aria-label="Upload images, PDF, or ZIP files"
          onChange={handleFilesSelected}
        />

        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {attachments.map((a) => (
              <div
                key={a.id}
                className="inline-flex items-center gap-1.5 pl-2 pr-1 py-1 rounded-md border border-border bg-background text-xs max-w-full"
              >
                {a.kind === 'repo' ? (
                  <FolderGit2 className="size-3.5 shrink-0 text-muted-foreground" />
                ) : (
                  fileIcon(a.label)
                )}
                <span className="truncate max-w-[200px] sm:max-w-[280px]" title={a.label}>
                  {a.label}
                </span>
                {a.sizeBytes != null && (
                  <span className="text-muted-foreground shrink-0">{formatBytes(a.sizeBytes)}</span>
                )}
                <button
                  type="button"
                  onClick={() => removeAttachment(a.id)}
                  className="p-0.5 rounded hover:bg-secondary text-muted-foreground hover:text-foreground"
                  aria-label="Remove attachment"
                >
                  <X className="size-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2 mb-3">
          <Popover open={attachOpen} onOpenChange={setAttachOpen}>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="shrink-0"
                disabled={isLoading}
                aria-label="Add sources: files or repository link"
              >
                <Paperclip className="size-4" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80 sm:w-96" align="start">
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-semibold text-foreground mb-1">Upload files</p>
                  <p className="text-xs text-muted-foreground mb-2">
                    Images, PDF, or ZIP archives (multiple files allowed).
                  </p>
                  <Button
                    type="button"
                    variant="secondary"
                    className="w-full gap-2"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Paperclip className="size-4" />
                    Choose files
                  </Button>
                </div>
                <div className="h-px bg-border" />
                <div className="space-y-2">
                  <Label htmlFor="repo-url" className="flex items-center gap-2 text-sm font-semibold">
                    <Link2 className="size-3.5" />
                    Repository link
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Paste a Git hosting URL (GitHub, GitLab, Bitbucket, etc.)
                  </p>
                  <Input
                    id="repo-url"
                    type="url"
                    inputMode="url"
                    placeholder="https://github.com/org/repo"
                    value={repoUrlInput}
                    onChange={(e) => setRepoUrlInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addRepoUrl();
                      }
                    }}
                  />
                  <Button
                    type="button"
                    className="w-full gap-2"
                    onClick={addRepoUrl}
                    disabled={!repoUrlInput.trim() || !isLikelyRepoUrl(repoUrlInput)}
                  >
                    <FolderGit2 className="size-4" />
                    Add repository
                  </Button>
                </div>
              </div>
            </PopoverContent>
          </Popover>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a question, or add sources with the paperclip..."
            aria-label="Chat message"
            className="flex-1 bg-secondary border border-border rounded-lg px-4 py-3 text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent transition-all min-h-[44px]"
            disabled={isLoading}
          />
          <Button
            type="button"
            onClick={handleSend}
            disabled={(!input.trim() && attachments.length === 0) || isLoading}
            className="shrink-0 h-11 px-5"
          >
            <Send size={18} />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Attachments are listed above before you send. Demo mode: files are not uploaded to a server yet.
        </p>
      </div>
    </motion.div>
  );
}
