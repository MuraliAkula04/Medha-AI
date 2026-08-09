'use client';

import {
  ArrowRight,
  BookOpen,
  Brain,
  Languages,
  Mic,
  Sparkles,
} from 'lucide-react';
import { motion } from 'motion/react';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
  ...props
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div
      ref={ref}
      {...props}
      className="relative flex min-h-screen w-full flex-col overflow-hidden bg-[#05080d] text-white"
    >
      {/* =========================================================
          AMBIENT BACKGROUND
      ========================================================= */}

      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {/* Warm center glow */}
        <motion.div
          className="absolute left-1/2 top-[25%] h-[500px] w-[700px] -translate-x-1/2 rounded-full blur-[160px]"
          style={{
            background:
              'radial-gradient(circle, rgba(245,158,11,0.10), rgba(14,165,233,0.05) 45%, transparent 70%)',
          }}
          animate={{
            opacity: [0.5, 0.8, 0.5],
            scale: [0.95, 1.05, 0.95],
          }}
          transition={{
            duration: 6,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />

        {/* Left blue glow */}
        <motion.div
          className="absolute -left-40 top-[45%] h-[350px] w-[500px] rounded-full bg-cyan-500/[0.035] blur-[130px]"
          animate={{
            x: [0, 80, 0],
            opacity: [0.3, 0.7, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />

        {/* Right green glow */}
        <motion.div
          className="absolute -right-40 top-[45%] h-[350px] w-[500px] rounded-full bg-emerald-500/[0.035] blur-[130px]"
          animate={{
            x: [0, -80, 0],
            opacity: [0.3, 0.65, 0.3],
          }}
          transition={{
            duration: 9,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />

        {/* Tiny floating particles */}
        <FloatingParticle className="left-[12%] top-[24%]" delay={0} />
        <FloatingParticle className="left-[22%] top-[62%]" delay={1.4} />
        <FloatingParticle className="right-[17%] top-[27%]" delay={2.1} />
        <FloatingParticle className="right-[25%] top-[66%]" delay={0.8} />
        <FloatingParticle className="left-[40%] top-[18%]" delay={2.8} />
      </div>

      {/* =========================================================
          HEADER
      ========================================================= */}

      <header className="relative z-30 flex h-[68px] items-center justify-between border-b border-white/[0.055] px-5 md:px-8">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <motion.div
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-amber-300/20 bg-gradient-to-br from-amber-400/20 to-white/[0.04] shadow-[0_0_30px_rgba(245,158,11,0.08)]"
            animate={{
              boxShadow: [
                '0 0 20px rgba(245,158,11,0.05)',
                '0 0 35px rgba(245,158,11,0.14)',
                '0 0 20px rgba(245,158,11,0.05)',
              ],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
            }}
          >
            <Sparkles className="h-[17px] w-[17px] text-amber-300" />
          </motion.div>

          <div>
            <div className="text-[15px] font-semibold tracking-tight">
              Medha AI
            </div>

            <div className="text-[10px] tracking-wide text-white/35">
              Voice Learning Companion
            </div>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          <div className="hidden text-[11px] font-semibold tracking-[0.18em] text-white/55 sm:block">
            BUILT WITH{' '}
            <span className="text-amber-300/90">
              LIVEKIT AGENTS
            </span>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.025] px-3 py-1.5 backdrop-blur-xl">
            <span className="text-amber-300">
              <Sparkles className="h-3.5 w-3.5" />
            </span>

            <span className="text-[11px] text-white/55">
              Memory Active
            </span>

            <motion.span
              className="h-1.5 w-1.5 rounded-full bg-emerald-400"
              animate={{
                opacity: [0.45, 1, 0.45],
                scale: [0.9, 1.15, 0.9],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
              }}
            />
          </div>
        </div>
      </header>

      {/* =========================================================
          MAIN CONTENT
      ========================================================= */}

      <main className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 flex-col items-center px-5 pb-12 pt-12 md:pt-16">
        {/* =====================================================
            SONIC WAVES
        ===================================================== */}

        <div className="pointer-events-none absolute left-1/2 top-[170px] h-[190px] w-[150vw] -translate-x-1/2 overflow-hidden opacity-90">
          <SonicWave
            color="#f59e0b"
            secondaryColor="#38bdf8"
            delay={0}
          />

          <SonicWave
            color="#38bdf8"
            secondaryColor="#34d399"
            delay={0.8}
            opacity={0.45}
          />

          <SonicWave
            color="#fbbf24"
            secondaryColor="#60a5fa"
            delay={1.5}
            opacity={0.25}
          />
        </div>

        {/* =====================================================
            HERO ICON
        ===================================================== */}

        <motion.div
          className="relative z-10 mb-7 flex h-[72px] w-[72px] items-center justify-center rounded-[22px] border border-amber-300/15 bg-gradient-to-br from-amber-400/[0.16] via-white/[0.045] to-transparent shadow-[0_0_70px_rgba(245,158,11,0.08)] backdrop-blur-xl"
          initial={{ opacity: 0, y: 12, scale: 0.92 }}
          animate={{
            opacity: 1,
            y: 0,
            scale: 1,
          }}
          transition={{
            duration: 0.6,
            ease: 'easeOut',
          }}
        >
          <motion.div
            className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-300 to-amber-500 text-black shadow-[0_0_35px_rgba(245,158,11,0.28)]"
            animate={{
              boxShadow: [
                '0 0 25px rgba(245,158,11,0.18)',
                '0 0 45px rgba(245,158,11,0.38)',
                '0 0 25px rgba(245,158,11,0.18)',
              ],
            }}
            transition={{
              duration: 2.5,
              repeat: Infinity,
            }}
          >
            <Sparkles className="h-6 w-6" />
          </motion.div>
        </motion.div>

        {/* =====================================================
            HEADING
        ===================================================== */}

        <motion.div
          className="relative z-10 max-w-4xl text-center"
          initial={{ opacity: 0, y: 18 }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.65,
            delay: 0.1,
            ease: 'easeOut',
          }}
        >
          <h1 className="text-[42px] font-semibold leading-[1.05] tracking-[-0.055em] text-white sm:text-5xl md:text-6xl lg:text-[64px]">
            What would you like to{' '}
            <span className="bg-gradient-to-r from-amber-200 via-amber-400 to-orange-300 bg-clip-text text-transparent">
              learn?
            </span>
          </h1>

          <p className="mx-auto mt-5 max-w-2xl text-sm leading-6 text-white/48 sm:text-base md:text-[17px] md:leading-7">
            Talk naturally with Medha AI. Ask questions,
            understand concepts, practice English, or explore
            something new.
          </p>
        </motion.div>

        {/* =====================================================
            START BUTTON
        ===================================================== */}

        <motion.div
          className="relative z-20 mt-9"
          initial={{
            opacity: 0,
            scale: 0.94,
          }}
          animate={{
            opacity: 1,
            scale: 1,
          }}
          transition={{
            duration: 0.5,
            delay: 0.25,
          }}
        >
          {/* button glow */}
          <motion.div
            className="absolute inset-0 rounded-full bg-amber-400/20 blur-2xl"
            animate={{
              opacity: [0.25, 0.55, 0.25],
              scale: [0.9, 1.08, 0.9],
            }}
            transition={{
              duration: 2.4,
              repeat: Infinity,
            }}
          />

          <Button
            size="lg"
            onClick={onStartCall}
            className="group relative h-14 rounded-full border border-amber-200/20 bg-gradient-to-r from-amber-200 via-amber-300 to-orange-300 px-8 text-[15px] font-semibold text-[#17120a] shadow-[0_10px_50px_rgba(245,158,11,0.16)] transition-all duration-300 hover:scale-[1.045] hover:shadow-[0_12px_60px_rgba(245,158,11,0.3)]"
          >
            <Mic className="mr-2.5 h-[18px] w-[18px] transition-transform duration-300 group-hover:scale-110" />

            {startButtonText || 'Start Learning'}

            <ArrowRight className="ml-2 h-4 w-4 opacity-50 transition-all duration-300 group-hover:translate-x-1 group-hover:opacity-100" />
          </Button>
        </motion.div>

        {/* =====================================================
            FEATURE CARDS
        ===================================================== */}

        <div className="relative z-20 mt-16 grid w-full max-w-[900px] grid-cols-1 gap-3 sm:grid-cols-3">
          <FeatureCard
            icon={<Brain className="h-[19px] w-[19px]" />}
            title="Learn"
            description="Understand difficult concepts with ease"
            color="amber"
            delay={0.35}
          />

          <FeatureCard
            icon={<BookOpen className="h-[19px] w-[19px]" />}
            title="Practice"
            description="Test yourself with questions & quizzes"
            color="blue"
            delay={0.45}
          />

          <FeatureCard
            icon={<Languages className="h-[19px] w-[19px]" />}
            title="Explore"
            description="Learn across languages and topics"
            color="green"
            delay={0.55}
          />
        </div>

        {/* =====================================================
            LANGUAGES
        ===================================================== */}

        <motion.div
          className="relative z-10 mt-8 flex flex-wrap items-center justify-center gap-2.5 text-xs"
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          transition={{
            delay: 0.7,
          }}
        >
          <span className="text-white/25">
            Try speaking in
          </span>

          <button className="font-medium text-amber-300 transition-colors hover:text-amber-200">
            English
          </button>

          <span className="text-white/15">•</span>

          <button className="text-white/55 transition-colors hover:text-cyan-300">
            తెలుగు
          </button>

          <span className="text-white/15">•</span>

          <button className="text-white/55 transition-colors hover:text-emerald-300">
            हिन्दी
          </button>
        </motion.div>
      </main>

      {/* =========================================================
          FOOTER
      ========================================================= */}

      <footer className="relative z-20 flex items-center justify-center pb-5">
        <p className="text-[11px] tracking-wide text-white/20">
          Medha AI
          <span className="mx-2 text-white/10">
            •
          </span>
          Learning & Literacy
        </p>
      </footer>

      {/* =========================================================
          THEME BUTTON
      ========================================================= */}

      <button
        aria-label="Theme"
        className="absolute bottom-5 left-5 z-30 flex h-10 w-10 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.025] text-white/55 backdrop-blur-xl transition-all duration-200 hover:border-amber-300/20 hover:bg-amber-300/[0.06] hover:text-amber-300"
      >
        <span className="text-lg">☼</span>
      </button>
    </div>
  );
};

/* =============================================================
   FEATURE CARD
============================================================= */

function FeatureCard({
  icon,
  title,
  description,
  color,
  delay,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: 'amber' | 'blue' | 'green';
  delay: number;
}) {
  const colors = {
    amber: {
      border: 'hover:border-amber-400/30',
      icon: 'border-amber-300/10 bg-amber-300/[0.08] text-amber-300',
      glow: 'group-hover:bg-amber-400/[0.035]',
      arrow:
        'border-amber-300/30 text-amber-300 group-hover:bg-amber-300/10',
    },

    blue: {
      border: 'hover:border-blue-400/30',
      icon: 'border-blue-300/10 bg-blue-300/[0.08] text-blue-300',
      glow: 'group-hover:bg-blue-400/[0.035]',
      arrow:
        'border-blue-300/30 text-blue-300 group-hover:bg-blue-300/10',
    },

    green: {
      border: 'hover:border-emerald-400/30',
      icon: 'border-emerald-300/10 bg-emerald-300/[0.08] text-emerald-300',
      glow: 'group-hover:bg-emerald-400/[0.035]',
      arrow:
        'border-emerald-300/30 text-emerald-300 group-hover:bg-emerald-300/10',
    },
  };

  const theme = colors[color];

  return (
    <motion.div
      initial={{
        opacity: 0,
        y: 18,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        duration: 0.5,
        delay,
      }}
      whileHover={{
        y: -5,
      }}
      className={`group relative overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.018] p-5 backdrop-blur-xl transition-all duration-300 ${theme.border}`}
    >
      {/* Hover glow */}
      <div
        className={`absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100 ${theme.glow}`}
      />

      <div className="relative z-10">
        <div className="flex items-start justify-between">
          <div
            className={`flex h-11 w-11 items-center justify-center rounded-xl border ${theme.icon}`}
          >
            {icon}
          </div>

          <div
            className={`flex h-8 w-8 items-center justify-center rounded-full border text-sm opacity-60 transition-all duration-300 group-hover:translate-x-1 group-hover:opacity-100 ${theme.arrow}`}
          >
            <ArrowRight className="h-3.5 w-3.5" />
          </div>
        </div>

        <div className="mt-5 text-[15px] font-semibold text-white/90">
          {title}
        </div>

        <div className="mt-1.5 max-w-[220px] text-xs leading-5 text-white/40">
          {description}
        </div>
      </div>
    </motion.div>
  );
}

/* =============================================================
   SONIC WAVE
============================================================= */

function SonicWave({
  color,
  secondaryColor,
  delay,
  opacity = 0.7,
}: {
  color: string;
  secondaryColor: string;
  delay: number;
  opacity?: number;
}) {
  return (
    <svg
      viewBox="0 0 1200 180"
      preserveAspectRatio="none"
      className="absolute inset-0 h-full w-full"
      style={{
        opacity,
      }}
    >
      <defs>
        <linearGradient
          id={`wave-${delay}`}
          x1="0%"
          y1="0%"
          x2="100%"
          y2="0%"
        >
          <stop
            offset="0%"
            stopColor={color}
            stopOpacity="0"
          />

          <stop
            offset="20%"
            stopColor={color}
            stopOpacity="0.65"
          />

          <stop
            offset="50%"
            stopColor="#ffffff"
            stopOpacity="0.8"
          />

          <stop
            offset="75%"
            stopColor={secondaryColor}
            stopOpacity="0.6"
          />

          <stop
            offset="100%"
            stopColor={secondaryColor}
            stopOpacity="0"
          />
        </linearGradient>

        <filter
          id={`blur-${delay}`}
          x="-20%"
          y="-100%"
          width="140%"
          height="300%"
        >
          <feGaussianBlur
            stdDeviation="1.8"
          />
        </filter>
      </defs>

      {[0, 1, 2, 3].map((index) => (
        <motion.path
          key={index}
          d={`
            M -50 90
            C 80 ${65 + index * 6},
              150 ${115 - index * 5},
              280 90
            S 470 ${65 + index * 7},
              600 90
            S 820 ${115 - index * 5},
              940 90
            S 1120 ${65 + index * 6},
              1250 90
          `}
          fill="none"
          stroke={`url(#wave-${delay})`}
          strokeWidth={index === 1 ? 1.5 : 1}
          filter={`url(#blur-${delay})`}
          animate={{
            d: [
              `
                M -50 90
                C 80 ${65 + index * 6},
                  150 ${115 - index * 5},
                  280 90
                S 470 ${65 + index * 7},
                  600 90
                S 820 ${115 - index * 5},
                  940 90
                S 1120 ${65 + index * 6},
                  1250 90
              `,
              `
                M -50 90
                C 80 ${110 - index * 4},
                  170 ${55 + index * 5},
                  300 90
                S 500 ${118 - index * 6},
                  620 90
                S 800 ${55 + index * 5},
                  950 90
                S 1120 ${110 - index * 4},
                  1250 90
              `,
              `
                M -50 90
                C 80 ${65 + index * 6},
                  150 ${115 - index * 5},
                  280 90
                S 470 ${65 + index * 7},
                  600 90
                S 820 ${115 - index * 5},
                  940 90
                S 1120 ${65 + index * 6},
                  1250 90
              `,
            ],
            opacity: [0.35, 0.8, 0.35],
          }}
          transition={{
            duration: 4 + index * 0.6,
            delay: delay + index * 0.15,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}
    </svg>
  );
}

/* =============================================================
   FLOATING PARTICLE
============================================================= */

function FloatingParticle({
  className,
  delay,
}: {
  className: string;
  delay: number;
}) {
  return (
    <motion.span
      className={`absolute h-1 w-1 rounded-full bg-amber-300/40 ${className}`}
      animate={{
        y: [0, -18, 0],
        x: [0, 5, 0],
        opacity: [0.15, 0.65, 0.15],
      }}
      transition={{
        duration: 4,
        delay,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    />
  );
}