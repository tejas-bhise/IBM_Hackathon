'use client';

import Link from 'next/link';
import {
  ArrowRight,
  Lock,
  Zap,
  Shield,
  MessageCircle,
  Sparkles,
  Cpu,
  Radar,
} from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { LandingBackground } from '@/components/landing/landing-background';

const ease = [0.22, 1, 0.36, 1] as const;

export default function Home() {
  const reduceMotion = useReducedMotion();

  const trans = reduceMotion
    ? { duration: 0 }
    : { duration: 0.65, ease };

  const stagger = reduceMotion ? 0 : 0.09;

  const fadeUp = {
    hidden: { opacity: 0, y: 28 },
    visible: {
      opacity: 1,
      y: 0,
      transition: trans,
    },
  };

  const container = {
    hidden: {},
    visible: {
      transition: { staggerChildren: stagger, delayChildren: reduceMotion ? 0 : 0.08 },
    },
  };

  return (
    <div className="relative min-h-screen flex flex-col overflow-x-hidden">
      <LandingBackground />

      {/* Header */}
      <motion.header
        initial={reduceMotion ? false : { opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={reduceMotion ? { duration: 0 } : { duration: 0.55, ease }}
        className="sticky top-0 z-50 border-b border-border/60 bg-background/70 backdrop-blur-xl backdrop-saturate-150 supports-[backdrop-filter]:bg-background/55"
      >
        <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent opacity-80" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <motion.div
            className="flex items-center gap-3"
            whileHover={reduceMotion ? undefined : { scale: 1.02 }}
            transition={{ type: 'spring', stiffness: 400, damping: 24 }}
          >
            <div className="relative">
              <div className="absolute inset-0 rounded-xl bg-accent/40 blur-lg opacity-70 motion-reduce:opacity-0" />
              <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-accent via-accent to-violet-600 flex items-center justify-center shadow-lg shadow-accent/25 ring-1 ring-white/20">
                <Lock size={18} className="text-white drop-shadow-sm" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground">SecureAI</h1>
              <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-medium">
                Intelligence Platform
              </p>
            </div>
          </motion.div>

          <div className="flex items-center gap-2 sm:gap-3">
            <motion.div whileHover={reduceMotion ? undefined : { y: -2 }} whileTap={reduceMotion ? undefined : { scale: 0.98 }}>
              <Link
                href="/dashboard/chat"
                className="group relative px-4 sm:px-5 py-2 rounded-xl font-semibold text-foreground flex items-center gap-2 overflow-hidden border border-border/80 bg-secondary/50 hover:bg-secondary hover:border-accent/35 hover:shadow-[0_0_24px_-8px_var(--accent)] transition-all duration-300"
              >
                <MessageCircle size={18} className="text-accent transition-transform group-hover:scale-110" />
                Chat
              </Link>
            </motion.div>
            <motion.div whileHover={reduceMotion ? undefined : { y: -2 }} whileTap={reduceMotion ? undefined : { scale: 0.98 }}>
              <Link
                href="/dashboard/upload"
                className="group relative px-4 sm:px-5 py-2 rounded-full font-semibold text-white flex items-center gap-2 bg-[#635BFF] hover:bg-[#635BFF]/90 transition-colors"
              >
                Dashboard
                <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
              </Link>
            </motion.div>
          </div>
        </div>
      </motion.header>

      <main className="flex-1 relative">
        {/* Hero */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20 lg:pt-24 lg:pb-28">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-14 lg:gap-16 items-center">
            <motion.div
              className="relative"
              variants={container}
              initial="hidden"
              animate="visible"
            >
              <motion.div variants={fadeUp}>
                <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-accent/25 bg-accent/10 text-accent text-sm font-semibold backdrop-blur-sm shadow-[inset_0_1px_0_0_oklch(1_0_0_/_0.06)] animate-float-badge motion-reduce:animate-none">
                  <Radar size={16} className="shrink-0" />
                  AI-Powered Security Analysis
                  <Sparkles size={14} className="opacity-80" />
                </span>
              </motion.div>

              <motion.h2
                variants={fadeUp}
                className="mt-8 text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tighter leading-tight text-foreground"
              >
                Detect threats <br />
                <span className="text-[#635BFF]">
                  before they ship.
                </span>
              </motion.h2>

              <motion.p variants={fadeUp} className="mt-6 text-lg text-muted-foreground leading-relaxed max-w-xl">
                Scan repos, documents, and links in one flow. The AI Project Intelligence Platform surfaces PII,
                secrets, and risky patterns, then explains what to fix in plain language.
              </motion.p>

              <motion.div variants={fadeUp} className="mt-10 flex flex-col sm:flex-row gap-4">
                <motion.div className="flex-1 sm:flex-initial" whileHover={reduceMotion ? undefined : { scale: 1.02 }} whileTap={reduceMotion ? undefined : { scale: 0.98 }}>
                  <Link
                    href="/dashboard/upload"
                    className="group flex w-full sm:w-auto items-center justify-center gap-2 px-6 py-3 rounded-full font-semibold bg-[#635BFF] text-white hover:bg-[#635BFF]/90 transition-colors"
                  >
                    Get Started
                    <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                  </Link>
                </motion.div>
                <motion.div className="flex-1 sm:flex-initial" whileHover={reduceMotion ? undefined : { scale: 1.02 }} whileTap={reduceMotion ? undefined : { scale: 0.98 }}>
                  <Link
                    href="/dashboard/chat"
                    className="flex w-full sm:w-auto items-center justify-center gap-2 px-6 py-3 rounded-full font-semibold bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
                  >
                    <MessageCircle size={18} />
                    Open Chat
                  </Link>
                </motion.div>
              </motion.div>

              <motion.div
                variants={fadeUp}
                className="mt-12 flex flex-wrap items-center gap-6 text-sm text-muted-foreground"
              >
                <div className="flex items-center gap-2">
                  <Cpu className="size-4 text-accent" />
                  <span>Gemini-ready</span>
                </div>
                <div className="hidden sm:block h-4 w-px bg-border" />
                <div className="flex items-center gap-2">
                  <Shield className="size-4 text-accent" />
                  <span>IBM Bob compatible</span>
                </div>
              </motion.div>
            </motion.div>

            {/* Feature cards */}
            <motion.div
              className="grid grid-cols-1 gap-4"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-40px' }}
              variants={container}
            >
              {[
                {
                  icon: Shield,
                  title: 'Security Scanning',
                  desc: 'Surface exposed credentials, API keys, and sensitive data across files and repos.',
                  accent: 'from-accent/20 to-transparent',
                },
                {
                  icon: Zap,
                  title: 'Real-Time Analysis',
                  desc: 'Instant feedback on risky patterns while you iterate, built for hackathon velocity.',
                  accent: 'from-violet-500/20 to-transparent',
                },
                {
                  icon: Lock,
                  title: 'Intelligent Fixes',
                  desc: 'Actionable fixes and architecture hints so judges see both depth and polish.',
                  accent: 'from-cyan-500/15 to-transparent',
                },
              ].map((card) => (
                <motion.article
                  key={card.title}
                  variants={fadeUp}
                  whileHover={
                    reduceMotion
                      ? undefined
                      : {
                          y: -6,
                          transition: { type: 'spring', stiffness: 400, damping: 22 },
                        }
                  }
                  className="group relative rounded-2xl border border-border/70 bg-card/40 backdrop-blur-md p-6 overflow-hidden shadow-lg shadow-black/5 dark:shadow-black/40 transition-colors hover:border-accent/45"
                >
                  <div
                    className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${card.accent} opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
                  />
                  <div className="relative flex gap-4">
                    <div className="shrink-0 w-12 h-12 rounded-xl bg-accent/15 flex items-center justify-center ring-1 ring-accent/20 group-hover:bg-accent/25 group-hover:scale-105 transition-all duration-300">
                      <card.icon size={24} className="text-accent" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-foreground mb-2">{card.title}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">{card.desc}</p>
                    </div>
                  </div>
                </motion.article>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Stats */}
        <motion.section
          className="relative border-y border-border/60 bg-secondary/30 backdrop-blur-sm"
          initial={reduceMotion ? false : { opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: reduceMotion ? 0 : 0.6 }}
        >
          <div className="absolute inset-0 bg-gradient-to-b from-accent/[0.03] via-transparent to-accent/[0.05]" />
          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-20">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-10">
              {[
                { value: '8', label: 'Issues surfaced (demo)', delay: 0 },
                { value: '42', label: 'Security score preview', delay: 0.06 },
                { value: '5', label: 'Modules mapped', delay: 0.12 },
              ].map((stat) => (
                <motion.div
                  key={stat.label}
                  initial={reduceMotion ? false : { opacity: 0, y: 16, scale: 0.97 }}
                  whileInView={{ opacity: 1, y: 0, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{
                    duration: reduceMotion ? 0 : 0.5,
                    delay: reduceMotion ? 0 : stat.delay,
                    ease,
                  }}
                  className="text-center group"
                >
                  <div className="relative inline-block">
                    <span className="absolute inset-0 blur-2xl bg-accent/25 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 motion-reduce:opacity-0" />
                    <div className="relative text-4xl lg:text-5xl font-bold text-foreground tabular-nums">
                      {stat.value}
                    </div>
                  </div>
                  <p className="mt-3 text-muted-foreground text-sm">{stat.label}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.section>

        {/* CTA */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
          <motion.div
            className="relative rounded-3xl border border-border bg-card p-10 sm:p-14 text-center shadow-lg"
            initial={reduceMotion ? false : { opacity: 0, y: 32 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: reduceMotion ? 0 : 0.65, ease }}
          >
            <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent opacity-50" />
            <div className="relative">
              <motion.div
                className="inline-flex items-center justify-center gap-2 mb-4 rounded-full border border-white/10 bg-background/30 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur-sm"
                initial={reduceMotion ? false : { scale: 0.9, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 1 }}
                viewport={{ once: true }}
              >
                <Sparkles className="size-3.5 text-accent" />
                Built to demo well on stage
              </motion.div>
              <h3 className="text-3xl sm:text-4xl font-bold text-foreground mb-4 tracking-tight">
                Ship a jaw-dropping demo
              </h3>
              <p className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
                Crisp UI, instant motion, and a clear story: scan, understand, act. That is what judges remember.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-stretch sm:items-center">
                <motion.div whileHover={reduceMotion ? undefined : { scale: 1.03 }} whileTap={reduceMotion ? undefined : { scale: 0.98 }}>
                  <Link
                    href="/dashboard/upload"
                    className="inline-flex w-full sm:w-auto items-center justify-center px-6 py-3 rounded-full font-semibold bg-[#635BFF] text-white hover:bg-[#635BFF]/90 transition-colors"
                  >
                    Access Dashboard
                  </Link>
                </motion.div>
                <motion.div whileHover={reduceMotion ? undefined : { scale: 1.03 }} whileTap={reduceMotion ? undefined : { scale: 0.98 }}>
                  <Link
                    href="/dashboard/chat"
                    className="inline-flex w-full sm:w-auto items-center justify-center gap-2 px-6 py-3 rounded-full font-semibold bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
                  >
                    <MessageCircle size={18} />
                    Open Chat
                  </Link>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </section>
      </main>

      <motion.footer
        initial={reduceMotion ? false : { opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="border-t border-border/60 bg-background/50 backdrop-blur-sm py-10"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-muted-foreground text-sm">
          <p>2026 SecureAI - IBM BOB Hackathon - polished UI, serious security story.</p>
        </div>
      </motion.footer>
    </div>
  );
}
