'use client';

import { useState } from 'react';
import { SecurityFinding } from '@/lib/types';
import { ChevronDown, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SecurityAuditorProps {
  findings: SecurityFinding[];
}

export function SecurityAuditor({ findings }: SecurityAuditorProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);

  const filteredFindings = selectedSeverity
    ? findings.filter((f) => f.severity === selectedSeverity)
    : findings;

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-500/10 border-red-500/30 text-red-500';
      case 'medium':
        return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500';
      case 'low':
        return 'bg-blue-500/10 border-blue-500/30 text-blue-500';
      default:
        return '';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertTriangle size={16} />;
      case 'medium':
        return <AlertCircle size={16} />;
      case 'low':
        return <Info size={16} />;
      default:
        return null;
    }
  };

  return (
    <div className="bg-secondary rounded-xl border border-border overflow-hidden">
      <div className="p-6 border-b border-border">
        <h3 className="text-lg font-semibold text-foreground mb-4">Security Findings</h3>

        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setSelectedSeverity(null)}
            className={cn(
              'px-3 py-1 rounded-lg text-sm font-medium transition-colors',
              selectedSeverity === null
                ? 'bg-accent text-accent-foreground'
                : 'bg-background text-muted-foreground hover:text-foreground'
            )}
          >
            All ({findings.length})
          </button>
          <button
            onClick={() => setSelectedSeverity('high')}
            className={cn(
              'px-3 py-1 rounded-lg text-sm font-medium transition-colors flex items-center gap-2',
              selectedSeverity === 'high'
                ? 'bg-red-500/20 text-red-500 border border-red-500/30'
                : 'bg-background text-muted-foreground hover:text-foreground'
            )}
          >
            <AlertTriangle size={14} /> High ({findings.filter((f) => f.severity === 'high').length})
          </button>
          <button
            onClick={() => setSelectedSeverity('medium')}
            className={cn(
              'px-3 py-1 rounded-lg text-sm font-medium transition-colors flex items-center gap-2',
              selectedSeverity === 'medium'
                ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/30'
                : 'bg-background text-muted-foreground hover:text-foreground'
            )}
          >
            <AlertCircle size={14} /> Medium ({findings.filter((f) => f.severity === 'medium').length})
          </button>
          <button
            onClick={() => setSelectedSeverity('low')}
            className={cn(
              'px-3 py-1 rounded-lg text-sm font-medium transition-colors flex items-center gap-2',
              selectedSeverity === 'low'
                ? 'bg-blue-500/20 text-blue-500 border border-blue-500/30'
                : 'bg-background text-muted-foreground hover:text-foreground'
            )}
          >
            <Info size={14} /> Low ({findings.filter((f) => f.severity === 'low').length})
          </button>
        </div>
      </div>

      <div className="divide-y divide-border">
        {filteredFindings.length > 0 ? (
          filteredFindings.map((finding) => {
            const findingId = finding.id || `finding-${finding.file}-${finding.line}`;
            return (
              <div key={findingId} className="border-b border-border last:border-b-0">
                <button
                  onClick={() => setExpandedId(expandedId === findingId ? null : findingId)}
                  className="w-full p-4 hover:bg-background/50 transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    <ChevronDown
                      size={18}
                      className={cn('text-muted-foreground transition-transform', expandedId === findingId && 'rotate-180')}
                    />

                  <div className={cn('p-2 rounded-lg flex-shrink-0', getSeverityColor(finding.severity))}>
                    {getSeverityIcon(finding.severity)}
                  </div>

                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-foreground capitalize">
                      {finding.type.replace(/_/g, ' ').toLowerCase()}
                    </h4>
                    <p className="text-sm text-muted-foreground truncate">
                      {finding.file}:{finding.line}
                    </p>
                  </div>

                  <div className={cn('px-3 py-1 rounded-md text-xs font-semibold flex-shrink-0', getSeverityColor(finding.severity))}>
                    {finding.severity.charAt(0).toUpperCase() + finding.severity.slice(1)}
                  </div>
                </div>
                </button>

                {expandedId === findingId && (
                <div className="px-4 pb-4 bg-background/30 border-t border-border">
                  <div className="space-y-3">
                    {finding.content && (
                      <div>
                        <label className="text-xs font-semibold text-muted-foreground uppercase">Found Content</label>
                        <code className="block text-xs bg-background/50 rounded p-2 mt-1 text-foreground overflow-x-auto border border-border">
                          {finding.content}
                        </code>
                      </div>
                    )}

                    {finding.context && (
                      <div>
                        <label className="text-xs font-semibold text-muted-foreground uppercase">Context</label>
                        <code className="block text-xs bg-background/50 rounded p-2 mt-1 text-foreground overflow-x-auto border border-border">
                          {finding.context}
                        </code>
                      </div>
                    )}

                    <div>
                      <label className="text-xs font-semibold text-muted-foreground uppercase">Recommended Fix</label>
                      <p className="text-xs text-foreground mt-1 leading-relaxed">
                        {finding.fix || finding.suggestedFix || 'No fix suggestion available'}
                      </p>
                    </div>

                    <button className="w-full mt-2 px-3 py-2 bg-accent text-accent-foreground rounded-lg text-sm font-semibold hover:bg-accent/90 transition-colors">
                      Apply Fix
                    </button>
                  </div>
                </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="p-8 text-center">
            <p className="text-muted-foreground">No findings in this category</p>
          </div>
        )}
      </div>
    </div>
  );
}
