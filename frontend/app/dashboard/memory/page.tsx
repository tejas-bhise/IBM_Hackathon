'use client';

import { useEffect, useState, useMemo, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getMemory, type MemoryItem } from '@/lib/api';
import { useProjectStore } from '@/lib/store';
import { MemoryTimeline } from '@/components/dashboard/memory-timeline';
import { TrendingUp, AlertCircle, Zap, Shield, GitBranch, Loader } from 'lucide-react';

export const dynamic = 'force-dynamic';

function MemoryPageContent() {
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

  const [memoryItems, setMemoryItems] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) {
      setError('No project ID found. Please upload a project first.');
      setLoading(false);
      // Redirect to upload page after 2 seconds
      const timer = setTimeout(() => {
        router.push('/upload');
      }, 2000);
      return () => clearTimeout(timer);
    }

    let cancelled = false;
    const fetchMemory = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await getMemory(projectId);
        
        if (!cancelled) {
          // Combine all memory items from different categories
          const allItems: MemoryItem[] = [
            ...(response.recent_work || []),
            ...(response.features || []),
            ...(response.security || []),
            ...(response.refactors || []),
          ];
          
          // Sort by timestamp (newest first)
          allItems.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
          
          setMemoryItems(allItems);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load project memory.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchMemory();
    
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  // Calculate stats
  const securityEvents = memoryItems.filter((item) => item.category === 'security').length;
  const featureUpdates = memoryItems.filter((item) => item.category === 'feature').length;
  const refactorEvents = memoryItems.filter((item) => item.category === 'refactor').length;

  // Loading state
  if (loading) {
    return (
      <div className="p-4 lg:p-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col items-center justify-center py-20">
            <Loader className="w-12 h-12 text-accent animate-spin mb-4" />
            <p className="text-muted-foreground">Loading project memory...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-4 lg:p-8">
        <div className="max-w-5xl mx-auto">
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6 flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-destructive flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h2 className="font-bold text-destructive mb-1">Failed to load memory</h2>
              <p className="text-destructive/80">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (memoryItems.length === 0) {
    return (
      <div className="p-4 lg:p-8">
        <div className="max-w-5xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Project Memory</h1>
            <p className="text-muted-foreground">
              Complete timeline of project changes and milestones. Use this to quickly resume work and understand what changed during your absence.
            </p>
          </div>
          
          <div className="bg-secondary rounded-xl border border-border p-12 text-center">
            <TrendingUp size={48} className="mx-auto mb-4 text-muted-foreground opacity-40" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No project history available</h3>
            <p className="text-muted-foreground">
              Project memory will be populated as you work on your project and make changes.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8">
      <div className="max-w-5xl mx-auto">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Project Memory</h1>
          <p className="text-muted-foreground">
            Complete timeline of project changes and milestones. Use this to quickly resume work and understand what changed during your absence.
          </p>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-secondary rounded-lg border border-border p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase">Total Events</p>
                <p className="text-2xl font-bold text-foreground mt-1">{memoryItems.length}</p>
              </div>
              <TrendingUp size={24} className="text-accent opacity-20" />
            </div>
          </div>

          <div className="bg-secondary rounded-lg border border-green-500/20 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-green-500 uppercase">Features</p>
                <p className="text-2xl font-bold text-green-500 mt-1">{featureUpdates}</p>
              </div>
              <Zap size={24} className="text-green-500 opacity-20" />
            </div>
          </div>

          <div className="bg-secondary rounded-lg border border-red-500/20 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-red-500 uppercase">Security</p>
                <p className="text-2xl font-bold text-red-500 mt-1">{securityEvents}</p>
              </div>
              <Shield size={24} className="text-red-500 opacity-20" />
            </div>
          </div>

          <div className="bg-secondary rounded-lg border border-blue-500/20 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-blue-500 uppercase">Refactors</p>
                <p className="text-2xl font-bold text-blue-500 mt-1">{refactorEvents}</p>
              </div>
              <GitBranch size={24} className="text-blue-500 opacity-20" />
            </div>
          </div>
        </div>

        {/* Main timeline */}
        <div className="mb-8">
          <MemoryTimeline items={memoryItems} />
        </div>

        {/* Insights section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Latest activity */}
          <div className="bg-secondary rounded-xl border border-border p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Zap size={20} className="text-accent" />
              Latest Activity
            </h3>
            <div className="space-y-4">
              {memoryItems.slice(0, 3).map((item, index) => (
                <div key={`${item.timestamp}-${index}`} className="pb-4 border-b border-border last:border-b-0">
                  <p className="font-semibold text-foreground text-sm">{item.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{item.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Tips for resuming work */}
          <div className="bg-secondary rounded-xl border border-border p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <AlertCircle size={20} className="text-blue-500" />
              Resume Checklist
            </h3>
            <ul className="space-y-3">
              <li className="flex gap-3">
                <input
                  type="checkbox"
                  className="mt-1 w-4 h-4 rounded border-border cursor-pointer"
                  defaultChecked
                />
                <label className="text-sm text-foreground cursor-pointer">Review timeline for critical updates</label>
              </li>
              <li className="flex gap-3">
                <input type="checkbox" className="mt-1 w-4 h-4 rounded border-border cursor-pointer" />
                <label className="text-sm text-foreground cursor-pointer">Check security issues from audits</label>
              </li>
              <li className="flex gap-3">
                <input type="checkbox" className="mt-1 w-4 h-4 rounded border-border cursor-pointer" />
                <label className="text-sm text-foreground cursor-pointer">Run latest tests and builds</label>
              </li>
              <li className="flex gap-3">
                <input type="checkbox" className="mt-1 w-4 h-4 rounded border-border cursor-pointer" />
                <label className="text-sm text-foreground cursor-pointer">Review project understanding notes</label>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MemoryPage() {
  return (
    <Suspense
      fallback={
        <div className="p-4 lg:p-8">
          <div className="max-w-5xl mx-auto">
            <div className="flex flex-col items-center justify-center py-20">
              <Loader className="w-12 h-12 text-accent animate-spin mb-4" />
              <p className="text-muted-foreground">Loading project memory...</p>
            </div>
          </div>
        </div>
      }
    >
      <MemoryPageContent />
    </Suspense>
  );
}

// Made with Bob
