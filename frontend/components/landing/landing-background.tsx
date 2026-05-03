'use client';

export function LandingBackground() {
  return (
    <div
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      aria-hidden
    >
      <div className="absolute inset-0 bg-[linear-gradient(135deg,oklch(0.55_0.19_262.95_/_0.20),transparent_34%),linear-gradient(225deg,oklch(0.6_0.15_200_/_0.15),transparent_38%)] dark:bg-[linear-gradient(135deg,oklch(0.55_0.19_262.95_/_0.28),transparent_34%),linear-gradient(225deg,oklch(0.6_0.15_200_/_0.18),transparent_38%)]" />

      <div className="absolute inset-x-[-18%] top-[12%] h-36 rotate-[-8deg] bg-gradient-to-r from-transparent via-accent/18 to-transparent blur-2xl animate-hologram motion-reduce:animate-none" />
      <div className="absolute inset-x-[-10%] bottom-[22%] h-28 rotate-[6deg] bg-gradient-to-r from-transparent via-cyan-400/14 to-transparent blur-2xl animate-hologram motion-reduce:animate-none [animation-delay:1.5s]" />

      <div className="landing-grid-bg absolute inset-0 opacity-[0.35] dark:opacity-[0.2]" />
      <div className="absolute left-0 top-0 h-full w-px bg-gradient-to-b from-transparent via-accent/40 to-transparent opacity-40" />
      <div className="absolute right-0 top-0 h-full w-px bg-gradient-to-b from-transparent via-cyan-400/30 to-transparent opacity-30" />
      <div className="absolute inset-x-0 top-1/3 h-px bg-gradient-to-r from-transparent via-accent/25 to-transparent opacity-70" />

      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent/50 to-transparent opacity-60" />
    </div>
  );
}
