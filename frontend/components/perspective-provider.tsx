'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

export type Perspective = 'dev' | 'pm' | 'finance';

interface PerspectiveContextType {
  perspective: Perspective;
  setPerspective: (perspective: Perspective) => void;
}

const PerspectiveContext = createContext<PerspectiveContextType | undefined>(undefined);

export function PerspectiveProvider({ children }: { children: ReactNode }) {
  const [perspective, setPerspective] = useState<Perspective>('dev');

  return (
    <PerspectiveContext.Provider value={{ perspective, setPerspective }}>
      {children}
    </PerspectiveContext.Provider>
  );
}

export function usePerspective() {
  const context = useContext(PerspectiveContext);
  if (context === undefined) {
    throw new Error('usePerspective must be used within a PerspectiveProvider');
  }
  return context;
}
