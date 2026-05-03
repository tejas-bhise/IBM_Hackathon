import { Suspense } from 'react';
import { DashboardClient } from './DashboardClient';
import { Cpu } from 'lucide-react';

export const dynamic = 'force-dynamic';

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Cpu className="size-8 animate-spin text-accent" />
      </div>
    }>
      <DashboardClient />
    </Suspense>
  );
}