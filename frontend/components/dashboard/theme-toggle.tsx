'use client';

import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = mounted ? resolvedTheme === 'dark' : true;

  return (
    <div className="flex items-center gap-2 px-2">
      <Sun size={18} className="text-[#2D4CC8] fill-current" />
      <button
        type="button"
        role="switch"
        aria-checked={isDark}
        onClick={() => setTheme(isDark ? 'light' : 'dark')}
        className="relative inline-flex h-6 w-11 items-center rounded-full bg-[#E2E2E2] dark:bg-secondary/80 transition-colors focus-visible:outline-none"
      >
        <span className="sr-only">Toggle theme</span>
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition duration-200 ease-in-out ${
            isDark ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
      <Moon size={18} className="text-[#2D4CC8] fill-current" />
    </div>
  );
}
