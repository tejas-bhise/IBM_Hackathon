import { create } from 'zustand';

interface ProjectState {
  projectId: string | null;
  setProjectId: (id: string | null) => void;
  clearProjectId: () => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projectId: null,

  setProjectId: (id) => {
    set({ projectId: id });
    if (typeof window !== 'undefined') {
      if (id) {
        localStorage.setItem('project_id', id);
      } else {
        localStorage.removeItem('project_id');
      }
    }
  },

  clearProjectId: () => {
    set({ projectId: null });
    if (typeof window !== 'undefined') {
      localStorage.removeItem('project_id');
    }
  },
}));

/**
 * SSR-safe hook — reads project_id from:
 * 1. URL ?project_id=  (highest priority)
 * 2. Zustand store
 * 3. localStorage (hard-refresh fallback)
 */
export function useProjectId(): string | null {
  const storeId = useProjectStore((s) => s.projectId);

  if (typeof window !== 'undefined') {
    const urlId = new URLSearchParams(window.location.search).get('project_id');
    if (urlId) return urlId;
  }

  if (storeId) return storeId;

  if (typeof window !== 'undefined') {
    return localStorage.getItem('project_id');
  }

  return null;
}