'use client';

import { Bell, Coins, Code, LineChart, Briefcase, Users } from 'lucide-react';
import { ThemeToggle } from '@/components/dashboard/theme-toggle';
import { usePerspective, Perspective } from '@/components/perspective-provider';

export function Navbar() {
  const { perspective, setPerspective } = usePerspective();

  return (
    <div className="fixed top-0 right-0 left-0 lg:left-64 h-16 z-40 bg-background/72 backdrop-blur-xl backdrop-saturate-150 supports-[backdrop-filter]:bg-background/55">
      <div className="h-full px-6 flex items-center justify-end">

        <div className="flex items-center gap-6">
          {perspective === 'finance' && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 border border-border">
              <Coins size={14} className="text-accent" />
              <span className="text-xs font-medium">1,250 Bobcoins</span>
              <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden ml-2">
                <div className="h-full bg-accent w-[65%]" />
              </div>
            </div>
          )}
          
          <div className="flex items-center bg-secondary/50 p-1 rounded-full">
            {(['dev', 'pm', 'finance'] as Perspective[]).map((mode) => {
              const icons = {
                dev: <Code size={14} />,
                pm: <LineChart size={14} />,
                finance: <Briefcase size={14} />
              };
              const labels = {
                dev: 'Dev',
                pm: 'Lead',
                finance: 'Finance'
              };
              const isActive = perspective === mode;
              
              return (
                <button
                  key={mode}
                  onClick={() => setPerspective(mode)}
                  className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-[#635BFF] text-white shadow-sm'
                      : 'bg-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {isActive && icons[mode]}
                  {labels[mode]}
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2 border-l border-border pl-4">
            <ThemeToggle />
            <button className="p-2 rounded-lg border border-transparent hover:border-accent/30 hover:bg-secondary text-muted-foreground hover:text-foreground transition-all">
              <Bell size={18} />
            </button>
            <button className="flex items-center gap-3 pl-2 pr-2 py-1.5 rounded-lg border border-transparent hover:bg-secondary/60 transition-all text-left">
              <div className="w-8 h-8 rounded-full bg-secondary border border-border flex items-center justify-center overflow-hidden shrink-0">
                <Users size={16} className="text-muted-foreground" aria-hidden="true" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-foreground leading-none mb-1">Project Team</span>
                <span className="text-xs text-muted-foreground leading-none">Group project</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
