'use client';

import { Sidebar } from '@/components/dashboard/sidebar';
import { Navbar } from '@/components/dashboard/navbar';
import { PerspectiveProvider } from '@/components/perspective-provider';
import { FloatingConnectButton } from '@/components/dashboard/floating-connect-button';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex h-screen overflow-hidden bg-background">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[linear-gradient(135deg,oklch(0.55_0.19_262.95_/_0.13),transparent_28%),linear-gradient(225deg,oklch(0.6_0.15_200_/_0.10),transparent_34%)]" />
      <div className="dashboard-grid-bg pointer-events-none fixed inset-0 -z-10 opacity-80" />
      <div className="pointer-events-none fixed inset-x-0 top-16 -z-10 h-32 rotate-[-4deg] bg-gradient-to-r from-transparent via-accent/12 to-transparent blur-2xl animate-hologram motion-reduce:animate-none" />
      <PerspectiveProvider>
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden lg:ml-64">
          <Navbar />
          <main className="flex-1 overflow-auto mt-16 relative">
            {children}
          </main>
        </div>
        <FloatingConnectButton />
      </PerspectiveProvider>
    </div>
  );
}
