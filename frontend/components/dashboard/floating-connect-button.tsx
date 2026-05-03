'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Plus } from 'lucide-react';
import { motion } from 'framer-motion';

export function FloatingConnectButton() {
  const pathname = usePathname();

  // Don't show the button if we are already on the upload page
  if (pathname === '/dashboard/upload') {
    return null;
  }

  return (
    <motion.div 
      className="fixed bottom-8 right-8 z-50"
      initial={{ opacity: 0, scale: 0.8, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 400, damping: 25, delay: 0.2 }}
    >
      <Link
        href="/dashboard/upload"
        className="group flex items-center gap-2 px-5 py-3.5 bg-[#635BFF] text-white hover:brightness-110 rounded-full font-semibold shadow-[0_8px_30px_-4px_rgba(99,91,255,0.4)] hover:shadow-[0_12px_40px_-4px_rgba(99,91,255,0.5)] transition-all border border-white/20"
      >
        <Plus size={20} className="transition-transform group-hover:rotate-90 duration-300" />
        Connect another repo
      </Link>
    </motion.div>
  );
}
