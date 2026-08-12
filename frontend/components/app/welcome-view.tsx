'use client';

import { useCallback, useRef, useState } from 'react';
import { ArrowRight, Mic, Phone, PhoneCall, UserCheck, X } from 'lucide-react';
import { AnimatePresence, motion, useAnimationFrame } from 'motion/react';
import { EscalationDashboard } from '@/components/app/escalation-dashboard';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

const BAR_COUNT = 48;

function useWaveform(active: boolean) {
  const bars = useRef<number[]>(Array.from({ length: BAR_COUNT }, () => 0.08));
  const phases = useRef<number[]>(
    Array.from({ length: BAR_COUNT }, (_, i) => (i / BAR_COUNT) * Math.PI * 2)
  );
  const [, forceUpdate] = useState(0);

  useAnimationFrame((t) => {
    const time = t / 1000;
    bars.current = phases.current.map((phase, i) => {
      if (!active) {
        return 0.06 + Math.sin(time * 0.8 + phase) * 0.04;
      }
      const center = 1 - Math.abs((i / BAR_COUNT - 0.5) * 2);
      const wave1 = Math.sin(time * 3.1 + phase) * 0.5 + 0.5;
      const wave2 = Math.sin(time * 5.7 + phase * 1.3) * 0.3 + 0.5;
      const wave3 = Math.sin(time * 2.0 + phase * 0.7) * 0.4 + 0.5;
      return 0.08 + center * (wave1 * wave2 * wave3) * 0.88;
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
  const bars = useWaveform(hovered);

  // Phone Call Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showEscalationsModal, setShowEscalationsModal] = useState(false);
  const [phoneNum, setPhoneNum] = useState('+91 93466 98489');
  const [isCalling, setIsCalling] = useState(false);

  const handleStart = useCallback(() => {
    onStartCall();
  }, [onStartCall]);

  const handleStartPhoneCall = (e: React.FormEvent) => {
    e.preventDefault();
    setIsCalling(true);
    // Connect LiveKit voice agent after short ring animation
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
      {/* ── Noise texture ────────────────────────────────────────────────── */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.028]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          backgroundSize: '128px 128px',
        }}
      />

      {/* ── Subtle gradient ────────────────────────────────────────────── */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-x-0 top-0 z-0 h-[50vh]"
        style={{
          background:
            'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(99,102,241,0.09) 0%, transparent 70%)',
        }}
      />

      {/* ══ NAV ════════════════════════════════════════════════════════════ */}
      <header className="relative z-20 flex h-14 items-center justify-between border-b border-white/[0.06] px-6 md:px-10">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 ring-1 ring-indigo-500/20">
            <Mic className="h-[14px] w-[14px] text-indigo-400" />
          </div>
          <span className="text-[14px] font-semibold tracking-tight text-white/90">Medha AI</span>
          <span className="ml-0.5 rounded-full bg-white/[0.05] px-2 py-0.5 text-[10px] font-medium tracking-wide text-white/30 ring-1 ring-white/[0.07]">
            BETA
          </span>
        </div>

        <nav className="hidden items-center gap-6 text-[13px] text-white/40 sm:flex">
          <span className="cursor-default transition-colors hover:text-white/70">How it works</span>
          <span className="cursor-default transition-colors hover:text-white/70">Languages</span>
          <span className="cursor-default transition-colors hover:text-white/70">About</span>
        </nav>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowEscalationsModal(true)}
            className="flex items-center gap-1.5 rounded-full border border-purple-500/30 bg-purple-500/10 px-3.5 py-1 text-[11px] font-medium text-purple-300 transition-all hover:border-purple-500/50 hover:bg-purple-500/20"
          >
            <UserCheck className="h-3 w-3 text-purple-400" />
            <span>Human Escalations</span>
          </button>
          <button
            onClick={() => {
              setIsCalling(false);
              setIsModalOpen(true);
            }}
            className="flex items-center gap-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3.5 py-1 text-[11px] font-medium text-indigo-300 transition-all hover:border-indigo-500/50 hover:bg-indigo-500/20"
          >
            <PhoneCall className="h-3 w-3" />
            <span>Make Phone Call</span>
          </button>
          <LiveDot />
        </div>
      </header>

      {/* ══ HERO ═══════════════════════════════════════════════════════════ */}
      <main className="relative z-10 mx-auto flex w-full max-w-5xl flex-1 flex-col items-center justify-center px-6 py-20 md:py-28">
        {/* ── Label ── */}
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-6 flex items-center gap-2 text-[11px] font-medium tracking-[0.14em] text-white/30 uppercase"
        >
          <span className="h-px w-5 bg-white/20" />
          Learning &amp; Literacy · VoiceForBharat
          <span className="h-px w-5 bg-white/20" />
        </motion.div>

        {/* ── Headline ── */}
        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.06 }}
          className="max-w-3xl text-center text-[40px] leading-[1.08] font-semibold tracking-[-0.04em] text-white sm:text-5xl md:text-[60px]"
        >
          Your AI tutor, <span className="text-indigo-400">always there.</span>
        </motion.h1>

        {/* ── Subhead ── */}
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.13 }}
          className="mt-5 max-w-lg text-center text-[15px] leading-7 text-white/38"
        >
          Ask questions, understand concepts, take live quizzes. In Telugu, Hindi, or English —
          Medha adapts to you.
        </motion.p>

        {/* ── Waveform visualizer ── */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.22 }}
          className="my-12 flex w-full max-w-[480px] items-center justify-center"
          aria-hidden
        >
          <div className="relative flex h-[88px] w-full items-end justify-center gap-[3px]">
            {bars.current.map((h, i) => {
              const barH = Math.max(3, Math.round(h * 88));
              const alpha = hovered ? 0.35 + h * 0.65 : 0.1 + h * 0.18;
              const color = hovered ? `rgba(99,102,241,${alpha})` : `rgba(255,255,255,${alpha})`;
              return (
                <div
                  key={i}
                  className="flex-1 rounded-full"
                  style={{
                    height: barH,
                    minHeight: 3,
                    maxHeight: 88,
                    backgroundColor: color,
                    willChange: 'height, background-color',
                  }}
                />
              );
            })}
            {hovered && (
              <div
                aria-hidden
                className="pointer-events-none absolute inset-0 rounded-2xl"
                style={{
                  background:
                    'radial-gradient(ellipse 60% 100% at 50% 50%, rgba(99,102,241,0.08) 0%, transparent 70%)',
                }}
              />
            )}
          </div>
        </motion.div>

        {/* ── CTA BUTTONS ── */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="flex flex-wrap items-center justify-center gap-4"
        >
          <button
            id="start-call-button"
            onClick={handleStart}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            className="group relative flex h-12 items-center gap-2.5 overflow-hidden rounded-full bg-white px-6 text-[14px] font-semibold text-zinc-900 shadow-[0_1px_3px_rgba(0,0,0,0.3),0_6px_20px_rgba(0,0,0,0.25)] transition-all duration-150 hover:shadow-[0_2px_8px_rgba(0,0,0,0.4),0_8px_28px_rgba(0,0,0,0.3)] active:scale-[0.97]"
          >
            <motion.span
              className="relative flex h-5 w-5 items-center justify-center"
              animate={hovered ? { scale: [1, 1.15, 1] } : { scale: 1 }}
              transition={{ duration: 0.4, repeat: hovered ? Infinity : 0 }}
            >
              <Mic className="h-[15px] w-[15px]" />
            </motion.span>
            {startButtonText || 'Start talking'}
            <ArrowRight className="h-3.5 w-3.5 opacity-0 transition-all duration-200 group-hover:-mr-0.5 group-hover:opacity-50" />
          </button>

          <button
            onClick={() => {
              setIsCalling(false);
              setIsModalOpen(true);
            }}
            className="group relative flex h-12 items-center gap-2.5 rounded-full border border-indigo-400/40 bg-indigo-500/10 px-6 text-[14px] font-semibold text-indigo-200 backdrop-blur-xl transition-all duration-200 hover:border-indigo-400/70 hover:bg-indigo-500/20 active:scale-[0.97]"
          >
            <PhoneCall className="h-[15px] w-[15px] text-indigo-400" />
            <span>Make Phone Call</span>
          </button>
        </motion.div>

        {/* ── Language tags ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.48 }}
          className="mt-8 flex items-center gap-1.5"
        >
          {['English', 'తెలుగు', 'हिन्दी'].map((lang) => (
            <span
              key={lang}
              className="rounded-full border border-white/[0.08] px-3 py-1 text-[11px] text-white/30 transition-colors hover:border-white/15 hover:text-white/50"
            >
              {lang}
            </span>
          ))}
        </motion.div>

        {/* ═══ CAPABILITIES STRIP ══════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.5 }}
          className="mt-24 w-full"
        >
          <div className="mb-10 flex items-center gap-4">
            <div className="h-px flex-1 bg-white/[0.06]" />
            <span className="text-[10px] tracking-[0.2em] text-white/20 uppercase">
              What Medha can do
            </span>
            <div className="h-px flex-1 bg-white/[0.06]" />
          </div>

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

      {/* ══ FOOTER ═════════════════════════════════════════════════════════ */}
      <footer className="relative z-10 border-t border-white/[0.05] px-6 py-5 md:px-10">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4">
          <p className="text-[11px] text-white/18">
            Medha AI · Learning &amp; Literacy · 10 Days of Voice Agents
          </p>
          <div className="flex items-center gap-1.5 text-[11px] text-white/18">
            <span>Powered by</span>
            <span className="font-medium text-indigo-400/60">Murf Falcon TTS</span>
            <span>·</span>
            <span className="font-medium text-white/25">LiveKit Agents</span>
          </div>
        </div>
      </footer>

      {/* ══ SIMPLE CLEAN PHONE CALL MODAL ═════════════════════════════════ */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleCancelCall}
              className="absolute inset-0 bg-black/80 backdrop-blur-md"
            />

            {/* Modal Box */}
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
                /* STEP 1: ENTER PHONE NUMBER */
                <div>
                  <div className="mb-5 flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-indigo-500/30 bg-indigo-500/10 text-indigo-400">
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
                        className="w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-2.5 text-sm text-white placeholder-white/20 outline-none focus:border-indigo-500/50"
                      />
                    </div>

                    <div className="pt-2">
                      <button
                        type="submit"
                        className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white transition-all hover:bg-indigo-500 active:scale-[0.98]"
                      >
                        <Phone className="h-4 w-4" />
                        <span>Call Now</span>
                      </button>
                    </div>
                  </form>
                </div>
              ) : (
                /* STEP 2: DISPLAY CALLING SCREEN */
                <div className="flex flex-col items-center py-6 text-center">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1.2, repeat: Infinity }}
                    className="mb-4 flex h-20 w-20 items-center justify-center rounded-full border border-indigo-500/30 bg-indigo-500/20 text-indigo-400 shadow-[0_0_40px_rgba(99,102,241,0.4)]"
                  >
                    <Phone className="h-9 w-9" />
                  </motion.div>

                  <span className="animate-pulse text-xs font-medium tracking-widest text-indigo-400 uppercase">
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

      {/* Escalations Modal Overlay */}
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
        'group border border-white/[0.06] bg-[#09090b] p-6 transition-colors duration-200 hover:bg-white/[0.02]',
        isFirst ? 'rounded-t-xl sm:rounded-t-none sm:rounded-l-xl' : '',
        isLast ? 'rounded-b-xl sm:rounded-r-xl sm:rounded-b-none' : '',
      ].join(' ')}
    >
      <div
        className="mb-4 font-mono text-[10px] font-semibold tracking-widest"
        style={{ color: 'rgba(255,255,255,0.18)' }}
      >
        {number}
      </div>
      <h3 className="mb-2 text-[14px] font-semibold" style={{ color: 'rgba(255,255,255,0.80)' }}>
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
      <motion.span
        className="h-1.5 w-1.5 rounded-full bg-emerald-500"
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 1.8, repeat: Infinity }}
      />
      <span className="text-[11px] text-white/35">Live</span>
    </div>
  );
}
