'use client';

import { SecurityFinding } from '@/lib/types';

interface SecurityScorePanelProps {
  score: number;
  findings: SecurityFinding[];
}

export function SecurityScorePanel({ score, findings }: SecurityScorePanelProps) {
  // Normalize severity to lowercase for comparison
  const highSeverity = findings.filter((f) => f.severity.toLowerCase() === 'high').length;
  const mediumSeverity = findings.filter((f) => f.severity.toLowerCase() === 'medium').length;
  const lowSeverity = findings.filter((f) => f.severity.toLowerCase() === 'low').length;

  const total = highSeverity + mediumSeverity + lowSeverity || 1;
  const highPct = Math.round((highSeverity / total) * 100);
  const medPct = Math.round((mediumSeverity / total) * 100);
  const lowPct = 100 - highPct - medPct;

  const scoreColor = score >= 80 ? 'text-green-500' : score >= 50 ? 'text-yellow-500' : 'text-red-500';

  const gap = 2; // Size of gap between segments

  const getSegmentProps = (pct: number, start: number, color: string) => {
    if (pct === 0) return null;
    const dashLength = Math.max(0, pct - gap);
    const gapLength = 100 - dashLength;
    const offset = 100 - start;
    return (
      <circle
        cx="20"
        cy="20"
        r="15.915"
        fill="transparent"
        stroke={color}
        strokeWidth="6"
        strokeDasharray={`${dashLength} ${gapLength}`}
        strokeDashoffset={offset}
        className="transition-all duration-500 ease-in-out"
      />
    );
  };

  return (
    <div className="glass-panel rounded-2xl p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-lg font-bold text-foreground">Security Score</h3>
        <div className={`text-xl font-bold ${scoreColor}`}>
          {score}<span className="text-sm font-medium text-muted-foreground ml-0.5">/100</span>
        </div>
      </div>

      <div className="flex-1 flex flex-row items-center justify-center gap-10">
        <div className="relative w-32 h-32 flex-shrink-0 flex items-center justify-center">
          <svg viewBox="0 0 40 40" className="w-full h-full -rotate-90">
            {/* Background ring if total is 0 */}
            {highSeverity === 0 && mediumSeverity === 0 && lowSeverity === 0 && (
              <circle cx="20" cy="20" r="15.915" fill="transparent" stroke="currentColor" className="text-muted/20" strokeWidth="6" />
            )}
            
            {getSegmentProps(highPct, 0, '#ef4444')}
            {getSegmentProps(medPct, highPct, '#8AB4F8')}
            {getSegmentProps(lowPct, highPct + medPct, '#81C995')}
          </svg>
        </div>

        <div className="w-full max-w-[160px] space-y-4">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-3">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
              <span className="text-foreground">High Severity</span>
            </div>
            <span className="font-semibold text-red-500">{highSeverity}</span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-3">
              <div className="w-2.5 h-2.5 rounded-full bg-[#8AB4F8]" />
              <span className="text-foreground">Medium Severity</span>
            </div>
            <span className="font-medium text-foreground">{mediumSeverity}</span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-3">
              <div className="w-2.5 h-2.5 rounded-full bg-[#81C995]" />
              <span className="text-foreground">Low Severity</span>
            </div>
            <span className="font-medium text-foreground">{lowSeverity}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
