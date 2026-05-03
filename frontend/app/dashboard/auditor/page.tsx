'use client';

import { SecurityAuditor } from '@/components/dashboard/security-auditor';
import { SecurityIssuesPanel } from '@/components/dashboard/security-issues-panel';
import { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getAnalysis, SecurityIssue } from '@/lib/api';
import { useProjectStore } from '@/lib/store';
import { SecurityFinding } from '@/lib/types';

export default function AuditorPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
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

  const [activeTab, setActiveTab] = useState('issues');
  const [findings, setFindings] = useState<SecurityFinding[]>([]);
  const [securityScore, setSecurityScore] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSecurityData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (!projectId) {
          setError('No project selected. Please upload a project first.');
          setLoading(false);
          // Redirect to upload page after 2 seconds
          const timer = setTimeout(() => {
            router.push('/upload');
          }, 2000);
          return () => clearTimeout(timer);
        }

        const analysis = await getAnalysis(projectId);
        
        // Transform backend SecurityIssue[] to frontend SecurityFinding[]
        const transformedFindings: SecurityFinding[] = (analysis.issues || []).map((issue: SecurityIssue, index: number) => ({
          id: `issue-${index}`,
          type: issue.type.toLowerCase().replace(/_/g, '_'), // Keep backend format
          severity: issue.severity.toLowerCase() as 'high' | 'medium' | 'low',
          file: issue.file_path,
          line: issue.line_number,
          fix: issue.fix_suggestion,
          suggestedFix: issue.fix_suggestion, // Map fix to suggestedFix for compatibility
          content: '', // Not provided by backend
          context: '', // Not provided by backend
        }));

        setFindings(transformedFindings);
        setSecurityScore(analysis.security_score || 0);
      } catch (err) {
        console.error('Failed to fetch security data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load security data');
      } finally {
        setLoading(false);
      }
    };

    fetchSecurityData();
  }, [projectId, router]);

  const highSeverityCount = findings.filter((f) => f.severity === 'high').length;
  const mediumSeverityCount = findings.filter((f) => f.severity === 'medium').length;
  const lowSeverityCount = findings.filter((f) => f.severity === 'low').length;

  if (loading) {
    return (
      <div className="p-4 lg:p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Security & Privacy Auditor</h1>
            <p className="text-muted-foreground">
              Detailed analysis of all detected security issues and sensitive data in your codebase
            </p>
          </div>
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
              <p className="text-muted-foreground">Running security analysis...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 lg:p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Security & Privacy Auditor</h1>
            <p className="text-muted-foreground">
              Detailed analysis of all detected security issues and sensitive data in your codebase
            </p>
          </div>
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
            <p className="text-red-500 font-semibold mb-2">Error Loading Security Data</p>
            <p className="text-muted-foreground">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Security & Privacy Auditor</h1>
          <p className="text-muted-foreground">
            Detailed analysis of all detected security issues and sensitive data in your codebase
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-secondary rounded-lg border border-red-500/30 p-4">
            <div className="text-2xl font-bold text-red-500">{highSeverityCount}</div>
            <p className="text-sm text-muted-foreground mt-1">High Severity</p>
          </div>
          <div className="bg-secondary rounded-lg border border-yellow-500/30 p-4">
            <div className="text-2xl font-bold text-yellow-500">{mediumSeverityCount}</div>
            <p className="text-sm text-muted-foreground mt-1">Medium Severity</p>
          </div>
          <div className="bg-secondary rounded-lg border border-green-500/30 p-4">
            <div className="text-2xl font-bold text-green-500">{lowSeverityCount}</div>
            <p className="text-sm text-muted-foreground mt-1">Low Severity</p>
          </div>
          <div className="bg-secondary rounded-lg border border-border p-4">
            <div className="text-2xl font-bold text-foreground">{findings.length}</div>
            <p className="text-sm text-muted-foreground mt-1">Total Findings</p>
          </div>
        </div>

        {/* Tab navigation */}
        <div className="flex gap-2 mb-6 border-b border-border">
          <button
            onClick={() => setActiveTab('issues')}
            className={cn(
              'px-4 py-3 font-medium border-b-2 transition-colors',
              activeTab === 'issues'
                ? 'border-accent text-accent'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            Security Issues Panel
          </button>
          <button
            onClick={() => setActiveTab('detailed')}
            className={cn(
              'px-4 py-3 font-medium border-b-2 transition-colors',
              activeTab === 'detailed'
                ? 'border-accent text-accent'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            Detailed Audit Report
          </button>
        </div>

        {/* Tab content */}
        {findings.length === 0 ? (
          <div className="bg-secondary rounded-xl border border-border p-12 text-center">
            <div className="text-green-500 text-5xl mb-4">✓</div>
            <h3 className="text-xl font-semibold text-foreground mb-2">No Security Issues Found</h3>
            <p className="text-muted-foreground">Your codebase appears to be secure!</p>
          </div>
        ) : (
          <>
            {activeTab === 'issues' && <SecurityIssuesPanel findings={findings} />}
            {activeTab === 'detailed' && <SecurityAuditor findings={findings} />}
          </>
        )}
      </div>
    </div>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}

// Made with Bob
