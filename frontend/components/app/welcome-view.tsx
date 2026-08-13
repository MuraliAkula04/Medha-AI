'use client';

import { useCallback, useRef, useState } from 'react';
import {
  ArrowRight,
  BarChart3,
  Mic,
  Phone,
  PhoneCall,
  Sparkles,
  UserCheck,
  X,
} from 'lucide-react';
import { AnimatePresence, motion, useAnimationFrame } from 'motion/react';
import { AnalyticsDashboard } from '@/components/app/analytics-dashboard';
import { EscalationDashboard } from '@/components/app/escalation-dashboard';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

const BAR_COUNT = 28;

function useWaveform() {
  const bars = useRef<number[]>(Array.from({ length: BAR_COUNT }, () => 0.15));
  const phases = useRef<number[]>(
    Array.from({ length: BAR_COUNT }, (_, i) => (i / BAR_COUNT) * Math.PI * 2)
  );
  const [, forceUpdate] = useState(0);

  useAnimationFrame((t) => {
    const time = t / 1000;
    bars.current = phases.current.map((phase, i) => {
      const center = 1 - Math.abs((i / BAR_COUNT - 0.5) * 2);
      const wave1 = Math.sin(time * 3.1 + phase) * 0.5 + 0.5;
      const wave2 = Math.sin(time * 5.7 + phase * 1.3) * 0.3 + 0.5;
      const wave3 = Math.sin(time * 2.0 + phase * 0.7) * 0.4 + 0.5;
      return 0.1 + center * (wave1 * wave2 * wave3) * 0.88;
    });
    forceUpdate((n) => n + 1);
  });

  return bars;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
  ...props
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [hovered, setHovered] = useState(false);
  const [sparkleRotated, setSparkleRotated] = useState(false);
  const bars = useWaveform();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showEscalationsModal, setShowEscalationsModal] = useState(false);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [phoneNum, setPhoneNum] = useState('+91 93466 98489');
  const [isCalling, setIsCalling] = useState(false);

  const handleStart = useCallback(() => {
    onStartCall();
  }, [onStartCall]);

  const handleStartPhoneCall = (e: React.FormEvent) => {
    e.preventDefault();
    setIsCalling(true);
    setTimeout(() => {
      onStartCall();
    }, 1500);
  };

  const handleCancelCall = () => {
    setIsCalling(false);
    setIsModalOpen(false);
  };

  return (
    <div
      ref={ref}
      {...props}
      className="relative flex min-h-screen w-full flex-col bg-[#09090b] text-white antialiased"
      style={{ backgroundColor: '#09090b' }}
    >
      {/* ── Dot Grid Background ─────────────────────────────────────────── */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-0"
        style={{
          backgroundImage: `radial-gradient(circle, rgba(255,255,255,0.055) 1px, transparent 1px)`,
          backgroundSize: '28px 28px',
        }}
      />

      {/* ── Noise texture ─────────────────────────────────────────────────── */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.022]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          backgroundSize: '128px 128px',
        }}
      />

      {/* ── Ambient purple glow ──────────────────────────────────────────── */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-x-0 top-0 z-0 h-[70vh]"
        style={{
          background:
            'radial-gradient(ellipse 80% 60% at 50% 5%, rgba(139,92,246,0.15) 0%, transparent 70%)',
        }}
      />

      {/* ══ NAV ══════════════════════════════════════════════════════════════ */}
      <header className="pointer-events-auto sticky top-0 z-50 flex h-14 w-full items-center justify-between border-b border-white/[0.06] bg-[#09090b]/90 px-6 backdrop-blur-md md:px-10">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 shadow-[0_0_12px_rgba(139,92,246,0.4)]">
            <Mic className="h-[13px] w-[13px] text-white" />
          </div>
          <span className="text-[14px] font-bold tracking-tight text-white">Medha AI</span>
          <span className="ml-0.5 rounded-full border border-violet-500/20 bg-violet-500/10 px-2 py-0.5 text-[9px] font-semibold tracking-widest text-violet-300/70 uppercase">
            BETA
          </span>
        </div>

        {/* Nav Links */}
        <nav className="hidden items-center gap-7 text-[13px] text-slate-400 sm:flex">
          {['How it works', 'Languages', 'About'].map((label) => (
            <span
              key={label}
              className="cursor-default transition-colors duration-200 hover:text-white"
            >
              {label}
            </span>
          ))}
        </nav>

        {/* Action Group */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setShowAnalyticsModal(true);
            }}
            onMouseDown={(e) => {
              e.stopPropagation();
              setShowAnalyticsModal(true);
            }}
            className="pointer-events-auto relative z-50 flex cursor-pointer select-none items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1 text-[11px] font-medium text-slate-300 transition-all hover:border-white/20 hover:bg-white/[0.07] active:scale-95"
          >
            <BarChart3 className="h-3 w-3 text-emerald-400" />
            <span>Call Analytics</span>
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setShowEscalationsModal(true);
            }}
            onMouseDown={(e) => {
              e.stopPropagation();
              setShowEscalationsModal(true);
            }}
            className="pointer-events-auto relative z-50 flex cursor-pointer select-none items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1 text-[11px] font-medium text-slate-300 transition-all hover:border-white/20 hover:bg-white/[0.07] active:scale-95"
          >
            <UserCheck className="h-3 w-3 text-purple-400" />
            <span>Human Escalations</span>
          </button>
          {/* Primary gradient button */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setIsCalling(false);
              setIsModalOpen(true);
            }}
            onMouseDown={(e) => {
              e.stopPropagation();
              setIsCalling(false);
              setIsModalOpen(true);
            }}
            className="pointer-events-auto relative z-50 flex cursor-pointer select-none items-center gap-1.5 rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 px-3.5 py-1.5 text-[11px] font-semibold text-white shadow-[0_0_16px_rgba(139,92,246,0.35)] transition-all hover:shadow-[0_0_22px_rgba(139,92,246,0.5)] active:scale-95"
          >
            <PhoneCall className="h-3 w-3" />
            <span>Make Phone Call</span>
          </button>
          <LiveDot />
        </div>
      </header>

      {/* ══ HERO ══════════════════════════════════════════════════════════════ */}
      <main className="relative z-10 mx-auto flex w-full max-w-5xl flex-1 flex-col items-center justify-center px-6 py-20 md:py-28">

        {/* ── Top Badge ── */}
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-8 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/[0.08] px-4 py-1.5 text-[11px] font-semibold tracking-[0.16em] text-violet-300/80 uppercase"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-violet-400" />
          Learning &amp; Literacy &nbsp;·&nbsp; VoiceForBharat
        </motion.div>

        {/* ── Headline ── */}
        <motion.h1
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.07 }}
          className="max-w-3xl text-center text-[42px] font-bold leading-[1.06] tracking-[-0.04em] text-white sm:text-5xl md:text-[64px]"
        >
          Your AI tutor,{' '}
          <span className="bg-gradient-to-r from-violet-400 via-purple-300 to-indigo-400 bg-clip-text text-transparent">
            always there.
          </span>
        </motion.h1>

        {/* ── Subhead ── */}
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.15 }}
          className="mt-5 max-w-lg text-center text-[15px] leading-7 text-slate-400"
        >
          Ask questions, understand concepts, take live quizzes. In{' '}
          <span className="font-medium text-white">Telugu</span>,{' '}
          <span className="font-medium text-white">Hindi</span>, or{' '}
          <span className="font-medium text-white">English</span> — Medha adapts to you.
        </motion.p>

        {/* ── Live Waveform Glassmorphism Card ── */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.24 }}
          className="my-10 w-full max-w-[480px] overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] p-5 shadow-[0_8px_32px_rgba(0,0,0,0.4)] backdrop-blur-md"
          aria-hidden
        >
          {/* Card Header */}
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600/60 to-indigo-600/60 ring-1 ring-white/10">
              <Mic className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-[12px] font-semibold text-white/80">Voice Assistant Active</p>
              <p className="text-[11px] text-slate-500">Listening for queries...</p>
            </div>
            <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-medium text-emerald-400">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              Live
            </span>
          </div>

          {/* Animated bars */}
          <div className="flex h-[52px] w-full items-end justify-center gap-[3px]">
            {bars.current.map((h, i) => {
              const barH = Math.max(4, Math.round(h * 52));
              const alpha = 0.3 + h * 0.7;
              const hue = 265 + i * 2;
              return (
                <div
                  key={i}
                  className="flex-1 rounded-full"
                  style={{
                    height: barH,
                    minHeight: 4,
                    maxHeight: 52,
                    background: `hsla(${hue}, 80%, 70%, ${alpha})`,
                    willChange: 'height',
                  }}
                />
              );
            })}
          </div>
        </motion.div>

        {/* ── CTA Button ── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.34 }}
        >
          <button
            id="start-call-button"
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              handleStart();
            }}
            onMouseDown={(e) => {
              e.stopPropagation();
              handleStart();
            }}
            onMouseEnter={() => {
              setHovered(true);
              setSparkleRotated(true);
            }}
            onMouseLeave={() => {
              setHovered(false);
              setSparkleRotated(false);
            }}
            className="group pointer-events-auto relative z-50 flex cursor-pointer select-none items-center gap-3 overflow-hidden rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 px-7 py-3.5 text-[15px] font-bold text-white shadow-[0_0_20px_rgba(139,92,246,0.25)] transition-all duration-200 hover:shadow-[0_0_30px_rgba(139,92,246,0.5)] active:scale-[0.97]"
          >
            {/* Shine sweep */}
            <span className="pointer-events-none absolute inset-0 translate-x-[-100%] skew-x-[-20deg] bg-white/10 transition-transform duration-500 group-hover:translate-x-[200%]" />
            <motion.span
              animate={sparkleRotated ? { rotate: 20, scale: 1.2 } : { rotate: 0, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              <Sparkles className="h-4 w-4" />
            </motion.span>
            {startButtonText || 'Start Learning Now'}
            <motion.span
              animate={hovered ? { x: 3 } : { x: 0 }}
              transition={{ duration: 0.2 }}
            >
              <ArrowRight className="h-4 w-4 opacity-70" />
            </motion.span>
          </button>
        </motion.div>

        {/* ── Language Selector Pills ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.46 }}
          className="mt-7 flex items-center gap-2"
        >
          {['English', 'తెలుగు', 'हिन्दी'].map((lang) => (
            <span
              key={lang}
              className="rounded-full border border-white/[0.09] px-3.5 py-1 text-[12px] font-medium text-slate-400 transition-all duration-200 hover:border-violet-400/40 hover:text-white"
            >
              {lang}
            </span>
          ))}
        </motion.div>

        {/* ─── Bottom Divider ─── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-20 flex w-full items-center gap-5"
        >
          <div className="h-px flex-1 bg-white/10" />
          <span className="text-[10px] font-semibold tracking-[0.22em] text-white/25 uppercase">
            What Medha Can Do
          </span>
          <div className="h-px flex-1 bg-white/10" />
        </motion.div>

        {/* ═══ CAPABILITIES STRIP ════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.58, duration: 0.5 }}
          className="mt-8 w-full"
        >
          <div className="grid grid-cols-1 gap-px sm:grid-cols-3">
            <Capability
              number="01"
              title="Explain anything"
              body="Ask about photosynthesis, recursion, the French Revolution — explained in plain language, then dig deeper."
              isFirst
            />
            <Capability
              number="02"
              title="Live quiz & practice"
              body="Medha fetches real questions from open databases, matched to your level. Instant feedback."
            />
            <Capability
              number="03"
              title="Remembers you"
              body="Your learning level, topics, common mistakes — stored and reused automatically across sessions."
              isLast
            />
          </div>
        </motion.div>
      </main>

      {/* ══ FOOTER ════════════════════════════════════════════════════════════ */}
      <footer className="relative z-10 border-t border-white/[0.05] px-6 py-5 md:px-10">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4">
          <p className="text-[11px] text-white/18">
            Medha AI · Learning &amp; Literacy · 10 Days of Voice Agents
          </p>
          <div className="flex items-center gap-1.5 text-[11px] text-white/18">
            <span>Powered by</span>
            <span className="font-medium text-violet-400/60">Murf Falcon TTS</span>
            <span>·</span>
            <span className="font-medium text-white/25">LiveKit Agents</span>
          </div>
        </div>
      </footer>

      {/* ══ PHONE CALL MODAL ══════════════════════════════════════════════════ */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleCancelCall}
              className="absolute inset-0 bg-black/80 backdrop-blur-md"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.94, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.94, y: 12 }}
              className="relative z-10 w-full max-w-sm overflow-hidden rounded-2xl border border-white/10 bg-[#0d0d12] p-6 shadow-2xl"
            >
              <button
                onClick={handleCancelCall}
                className="absolute top-4 right-4 rounded-full p-1 text-white/40 transition-colors hover:bg-white/10 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>

              {!isCalling ? (
                <div>
                  <div className="mb-5 flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-[0_0_16px_rgba(139,92,246,0.4)]">
                      <PhoneCall className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-white">Make Phone Call</h3>
                      <p className="text-xs text-white/40">Enter phone number to initiate call</p>
                    </div>
                  </div>

                  <form onSubmit={handleStartPhoneCall} className="space-y-4">
                    <div>
                      <label className="mb-1 block text-xs font-medium text-white/60">
                        Phone Number
                      </label>
                      <input
                        type="tel"
                        required
                        value={phoneNum}
                        onChange={(e) => setPhoneNum(e.target.value)}
                        placeholder="+91 93466 98489"
                        className="w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-2.5 text-sm text-white placeholder-white/20 outline-none focus:border-violet-500/50"
                      />
                    </div>
                    <div className="pt-2">
                      <button
                        type="submit"
                        className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 py-3 text-sm font-semibold text-white shadow-[0_0_16px_rgba(139,92,246,0.3)] transition-all hover:shadow-[0_0_24px_rgba(139,92,246,0.5)] active:scale-[0.98]"
                      >
                        <Phone className="h-4 w-4" />
                        <span>Call Now</span>
                      </button>
                    </div>
                  </form>
                </div>
              ) : (
                <div className="flex flex-col items-center py-6 text-center">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1.2, repeat: Infinity }}
                    className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-violet-600/30 to-indigo-600/30 text-violet-400 shadow-[0_0_40px_rgba(139,92,246,0.4)] ring-1 ring-violet-500/30"
                  >
                    <Phone className="h-9 w-9" />
                  </motion.div>
                  <span className="animate-pulse text-xs font-semibold tracking-widest text-violet-400 uppercase">
                    Calling...
                  </span>
                  <h3 className="mt-2 text-xl font-bold text-white">{phoneNum}</h3>
                  <p className="mt-1 text-xs text-white/40">Connecting Medha AI Voice Companion</p>
                  <div className="mt-6 w-full pt-2">
                    <button
                      onClick={handleCancelCall}
                      className="flex w-full items-center justify-center gap-2 rounded-xl bg-red-600/90 py-3 text-sm font-semibold text-white transition-all hover:bg-red-600 active:scale-[0.98]"
                    >
                      <X className="h-4 w-4" />
                      <span>End Call</span>
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Escalations Modal */}
      <AnimatePresence>
        {showEscalationsModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md"
          >
            <EscalationDashboard onClose={() => setShowEscalationsModal(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Analytics Modal */}
      <AnimatePresence>
        {showAnalyticsModal && <AnalyticsDashboard onClose={() => setShowAnalyticsModal(false)} />}
      </AnimatePresence>
    </div>
  );
};

function Capability({
  number,
  title,
  body,
  isFirst,
  isLast,
}: {
  number: string;
  title: string;
  body: string;
  isFirst?: boolean;
  isLast?: boolean;
}) {
  return (
    <div
      className={[
        'group border border-white/[0.06] bg-[#09090b] p-6 transition-colors duration-200 hover:bg-white/[0.025]',
        isFirst ? 'rounded-t-xl sm:rounded-t-none sm:rounded-l-xl' : '',
        isLast ? 'rounded-b-xl sm:rounded-r-xl sm:rounded-b-none' : '',
      ].join(' ')}
    >
      <div
        className="mb-4 font-mono text-[10px] font-semibold tracking-widest"
        style={{ color: 'rgba(139,92,246,0.5)' }}
      >
        {number}
      </div>
      <h3 className="mb-2 text-[14px] font-semibold" style={{ color: 'rgba(255,255,255,0.82)' }}>
        {title}
      </h3>
      <p className="text-[12px] leading-relaxed" style={{ color: 'rgba(255,255,255,0.32)' }}>
        {body}
      </p>
    </div>
  );
}

function LiveDot() {
  return (
    <div className="flex items-center gap-1.5 rounded-full border border-white/[0.07] bg-white/[0.03] px-2.5 py-1">
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
      <span className="text-[11px] text-white/35">Live</span>
    </div>
  );
}

