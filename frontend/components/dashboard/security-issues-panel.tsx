'use client';

import { useState } from 'react';
import { SecurityFinding } from '@/lib/types';
import { Copy, Check, Shield, AlertTriangle, AlertCircle, Info, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SecurityIssuesPanelProps {
  findings: SecurityFinding[];
}

export function SecurityIssuesPanel({ findings }: SecurityIssuesPanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string | null>(null);

  // Dynamic threat type labels - generate from actual types in findings
  const getThreatTypeLabel = (type: string): { label: string; icon: React.ReactNode; description: string } => {
    const typeKey = type.toLowerCase();
    
    // Common security issue types
    const knownTypes: Record<string, { label: string; icon: React.ReactNode; description: string }> = {
      sql_injection: {
        label: 'SQL Injection',
        icon: <AlertTriangle size={16} />,
        description: 'Vulnerable query construction pattern detected',
      },
      xss: {
        label: 'Cross-Site Scripting (XSS)',
        icon: <AlertTriangle size={16} />,
        description: 'Potential XSS vulnerability detected',
      },
      hardcoded_secret: {
        label: 'Hardcoded Secret',
        icon: <AlertTriangle size={16} />,
        description: 'Secret credentials found in code',
      },
      path_traversal: {
        label: 'Path Traversal',
        icon: <AlertCircle size={16} />,
        description: 'Potential directory traversal vulnerability',
      },
      command_injection: {
        label: 'Command Injection',
        icon: <AlertTriangle size={16} />,
        description: 'Potential command injection vulnerability',
      },
      insecure_deserialization: {
        label: 'Insecure Deserialization',
        icon: <AlertCircle size={16} />,
        description: 'Unsafe deserialization detected',
      },
      weak_crypto: {
        label: 'Weak Cryptography',
        icon: <AlertCircle size={16} />,
        description: 'Weak or outdated cryptographic algorithm',
      },
      email: {
        label: 'Exposed Email (PII)',
        icon: <AlertTriangle size={16} />,
        description: 'Personally identifiable information exposed in code',
      },
      phone: {
        label: 'Exposed Phone (PII)',
        icon: <AlertCircle size={16} />,
        description: 'Phone number exposed in code or comments',
      },
      api_key: {
        label: 'Hardcoded API Key',
        icon: <AlertTriangle size={16} />,
        description: 'Secret credentials committed to repository',
      },
    };

    // Return known type or generate generic label
    return knownTypes[typeKey] || {
      label: type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      icon: <Info size={16} />,
      description: 'Security issue detected',
    };
  };

  const getRiskColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return {
          bg: 'bg-red-500/10',
          border: 'border-red-500/30',
          text: 'text-red-500',
          badge: 'bg-red-600 text-white border-red-700',
        };
      case 'medium':
        return {
          bg: 'bg-yellow-500/10',
          border: 'border-yellow-500/30',
          text: 'text-yellow-500',
          badge: 'bg-yellow-600 text-white border-yellow-700',
        };
      case 'low':
        return {
          bg: 'bg-green-500/10',
          border: 'border-green-500/30',
          text: 'text-green-500',
          badge: 'bg-green-600 text-white border-green-700',
        };
      default:
        return {
          bg: 'bg-blue-500/10',
          border: 'border-blue-500/30',
          text: 'text-blue-500',
          badge: 'bg-blue-600 text-white border-blue-700',
        };
    }
  };

  const getRiskLabel = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'Critical Risk';
      case 'medium':
        return 'Medium Risk';
      case 'low':
        return 'Low Risk';
      default:
        return 'Safe';
    }
  };

  const filteredFindings = filterType
    ? findings.filter((f) => f.type === filterType)
    : findings;

  const threatTypes = Array.from(new Set(findings.map((f) => f.type)));

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6 mt-8">
      {/* Header with stats */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Shield className="text-muted-foreground/60" size={24} />
            <h3 className="text-xl font-bold text-foreground">Security Issues Detected</h3>
          </div>
          <div className="text-4xl font-bold text-red-500">{findings.length}</div>
        </div>

        {/* Threat type filters */}
        <div className="relative mb-6 pl-[36px]">
          {/* Base border */}
          <div className="absolute bottom-0 left-[36px] right-0 h-px bg-border/60" />
          
          <div className="flex gap-6 overflow-x-auto overflow-y-hidden scrollbar-hide relative z-10">
            <button
              onClick={() => setFilterType(null)}
              className={cn(
                'pb-3 text-sm font-medium transition-colors relative flex items-center gap-2 border-b-2 whitespace-nowrap',
                filterType === null
                  ? 'text-[#635BFF] border-[#635BFF]'
                  : 'text-muted-foreground border-transparent hover:text-foreground'
              )}
            >
              <span>All</span>
              <span className={cn(
                "px-2 py-0.5 rounded-full text-[10px] font-bold leading-none flex items-center justify-center min-w-[20px] h-[20px]",
                filterType === null ? "bg-[#635BFF] text-white" : "bg-secondary text-muted-foreground"
              )}>{findings.length}</span>
            </button>
            {threatTypes.map((type) => {
              const typeData = getThreatTypeLabel(type);
              const count = findings.filter((f) => f.type === type).length;
              
              return (
                <button
                  key={type}
                  onClick={() => setFilterType(type)}
                  className={cn(
                    'pb-3 text-sm font-medium transition-colors relative flex items-center gap-2 border-b-2 whitespace-nowrap',
                    filterType === type
                      ? 'text-[#635BFF] border-[#635BFF]'
                      : 'text-muted-foreground border-transparent hover:text-foreground'
                  )}
                >
                  {typeData.icon}
                  <span>{typeData.label}</span>
                  <span className={cn(
                    "px-2 py-0.5 rounded-full text-[10px] font-bold leading-none flex items-center justify-center min-w-[20px] h-[20px]",
                    filterType === type ? "bg-[#635BFF] text-white" : "bg-secondary text-muted-foreground"
                  )}>{count}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Issues list */}
      <div className="space-y-3 ml-[36px]">
        {filteredFindings.length > 0 ? (
          filteredFindings.map((finding) => {
            const findingId = finding.id || `finding-${finding.file}-${finding.line}`;
            const colors = getRiskColor(finding.severity);
            const threatInfo = getThreatTypeLabel(finding.type);

            return (
              <div
                key={findingId}
                className={cn(
                  'rounded-xl border transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_18px_48px_-30px_currentColor]',
                  expandedId === findingId
                    ? `bg-transparent ${colors.border} border-2`
                    : `bg-transparent ${colors.border} border`
                )}
              >
                <button
                  onClick={() => setExpandedId(expandedId === findingId ? null : findingId)}
                  className="w-full p-4 text-left hover:bg-secondary/30 transition-colors rounded-xl"
                >
                  <div className="flex items-center gap-4">
                    {/* Risk indicator */}
                    <div className={cn('p-2.5 rounded-lg flex-shrink-0', colors.bg, colors.text)}>
                      {threatInfo.icon}
                    </div>

                    {/* Issue details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h4 className={cn('font-semibold mb-1', colors.text)}>
                            {threatInfo.label}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            {threatInfo.description}
                          </p>
                          <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                            <code className="bg-secondary/50 px-2 py-1 rounded">
                              {finding.file}:{finding.line}
                            </code>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Risk badge & Chevron */}
                    <div className="flex items-center gap-4 flex-shrink-0">
                      <div
                        className={cn(
                          'px-3 py-1.5 rounded-full text-xs font-semibold border',
                          colors.badge
                        )}
                      >
                        {getRiskLabel(finding.severity)}
                      </div>
                      <ChevronDown
                        className={cn(
                          "text-muted-foreground transition-transform duration-300",
                          expandedId === findingId ? "rotate-180" : ""
                        )}
                        size={20}
                      />
                    </div>
                  </div>
                </button>

                {/* Expanded details */}
                {expandedId === findingId && (
                  <div className={cn('border-t p-4', colors.border)}>
                    <div className="space-y-4">
                      {/* Found content - only show if available */}
                      {finding.content && (
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-xs font-semibold text-muted-foreground uppercase">
                              Detected Content
                            </label>
                            <button
                              onClick={() => copyToClipboard(finding.content || '', `content-${findingId}`)}
                              className="p-1 hover:bg-background rounded transition-colors"
                              title="Copy to clipboard"
                            >
                              {copiedId === `content-${findingId}` ? (
                                <Check size={14} className="text-green-500" />
                              ) : (
                                <Copy size={14} className="text-muted-foreground" />
                              )}
                            </button>
                          </div>
                          <code className="block text-sm bg-background/50 rounded border border-border p-3 overflow-x-auto font-mono text-foreground">
                            {finding.content}
                          </code>
                        </div>
                      )}

                      {/* Code context - only show if available */}
                      {finding.context && (
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-xs font-semibold text-muted-foreground uppercase">
                              Code Context
                            </label>
                            <button
                              onClick={() => copyToClipboard(finding.context || '', `context-${findingId}`)}
                              className="p-1 hover:bg-background rounded transition-colors"
                              title="Copy to clipboard"
                            >
                              {copiedId === `context-${findingId}` ? (
                                <Check size={14} className="text-green-500" />
                              ) : (
                                <Copy size={14} className="text-muted-foreground" />
                              )}
                            </button>
                          </div>
                          <code className="block text-sm bg-background/50 rounded border border-border p-3 overflow-x-auto font-mono text-foreground">
                            {finding.context}
                          </code>
                        </div>
                      )}

                      {/* Suggested fix */}
                      <div>
                        <label className="text-xs font-semibold text-muted-foreground uppercase block mb-2">
                          Recommended Fix
                        </label>
                        <div className={cn(
                          'rounded border p-3 text-sm leading-relaxed',
                          colors.bg,
                          colors.border
                        )}>
                          <p className={cn('text-foreground', colors.text)}>
                            {finding.fix || finding.suggestedFix || 'No fix suggestion available'}
                          </p>
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="flex gap-2 pt-2">
                        <button
                          className={cn(
                            'flex-1 px-4 py-2 rounded-lg text-sm font-semibold transition-colors',
                            colors.badge
                          )}
                        >
                          Review Fix
                        </button>
                        <button className="flex-1 px-4 py-2 rounded-lg text-sm font-semibold bg-accent text-accent-foreground hover:bg-accent/90 transition-colors">
                          Mark as Fixed
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="rounded-xl border border-border bg-secondary p-8 text-center">
            <Shield className="mx-auto mb-3 text-green-500" size={32} />
            <h3 className="font-semibold text-foreground mb-1">No Issues Found</h3>
            <p className="text-muted-foreground">Your codebase looks secure!</p>
          </div>
        )}
      </div>
    </div>
  );
}
