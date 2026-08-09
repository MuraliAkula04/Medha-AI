'use client';

import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import {
  useAgent,
  useSessionContext,
  useSessionMessages,
} from '@livekit/components-react';

import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';

import { cn } from '@/lib/shadcn/utils';
import { TileLayout } from './tile-view';

interface FadeProps {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}

export function Fade({
  top = false,
  bottom = false,
  className,
}: FadeProps) {
  return (
    <div
      className={cn(
        'pointer-events-none h-4 bg-linear-to-b from-background to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className,
      )}
    />
  );
}

/* =========================================================
   PREMIUM SONIC WAVE
   ========================================================= */

function SonicWave({ state }: { state: string }) {
  const isSpeaking = state === 'speaking';
  const isListening = state === 'listening';
  const isThinking = state === 'thinking';
  const isConnecting = state === 'initializing';

  const active =
    isSpeaking || isListening || isThinking || isConnecting;

  const color = isSpeaking
    ? '#a855f7'
    : isListening
      ? '#22d3ee'
      : isThinking
        ? '#f59e0b'
        : isConnecting
          ? '#60a5fa'
          : '#71717a';

  const secondaryColor = isSpeaking
    ? '#ec4899'
    : isListening
      ? '#14b8a6'
      : isThinking
        ? '#facc15'
        : isConnecting
          ? '#818cf8'
          : '#52525b';

  const waveHeight = isSpeaking
    ? 58
    : isListening
      ? 34
      : isThinking
        ? 28
        : isConnecting
          ? 20
          : 10;

  const duration = isSpeaking
    ? 1.25
    : isListening
      ? 2.4
      : isThinking
        ? 2.8
        : 4;

  const createPath = (
    phase: number,
    amplitude: number,
    frequency: number,
  ) => {
    const points = 90;
    const width = 900;
    const center = 90;
    let path = '';

    for (let i = 0; i <= points; i++) {
      const x = (i / points) * width;
      const p = i / points;

      const envelope =
        0.35 + Math.sin(p * Math.PI) * 0.65;

      const y =
        center +
        Math.sin(
          p * Math.PI * 2 * frequency + phase,
        ) *
          amplitude *
          envelope +
        Math.sin(
          p * Math.PI * 4.1 * frequency -
            phase * 0.65,
        ) *
          amplitude *
          0.22;

      path += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
    }

    return path;
  };

  const waves = [
    {
      amplitude: waveHeight * 0.7,
      frequency: 1.05,
      opacity: 0.28,
      width: 1.05,
      delay: 0,
    },
    {
      amplitude: waveHeight * 0.88,
      frequency: 1.18,
      opacity: 0.34,
      width: 1.15,
      delay: 0.08,
    },
    {
      amplitude: waveHeight,
      frequency: 1.32,
      opacity: 0.46,
      width: 1.3,
      delay: 0.16,
    },
    {
      amplitude: waveHeight * 0.78,
      frequency: 1.48,
      opacity: 0.65,
      width: 1.65,
      delay: 0.24,
    },
    {
      amplitude: waveHeight * 0.55,
      frequency: 1.65,
      opacity: 0.9,
      width: 2.05,
      delay: 0.32,
    },
    {
      amplitude: waveHeight * 0.42,
      frequency: 1.82,
      opacity: 0.35,
      width: 1,
      delay: 0.4,
    },
  ];

  return (
    <div className="relative h-52 w-full max-w-[1180px] overflow-visible">
      {/* soft glow only — no grid and no card */}
      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/2 h-24 w-[65%] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[90px]"
        style={{
          background: `linear-gradient(90deg, transparent, ${color}, ${secondaryColor}, transparent)`,
        }}
        animate={{
          opacity: active ? [0.08, 0.22, 0.08] : 0.035,
          scaleX: active ? [0.9, 1.08, 0.9] : 1,
        }}
        transition={{
          duration: isSpeaking ? 1.1 : 2.8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      <svg
        viewBox="0 0 900 180"
        preserveAspectRatio="none"
        className="relative z-10 h-full w-full overflow-visible"
      >
        <defs>
          <linearGradient
            id="medhaWaveGradient"
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
              offset="18%"
              stopColor={color}
              stopOpacity="0.4"
            />
            <stop
              offset="42%"
              stopColor={secondaryColor}
              stopOpacity="0.85"
            />
            <stop
              offset="50%"
              stopColor="#ffffff"
              stopOpacity="0.95"
            />
            <stop
              offset="58%"
              stopColor={secondaryColor}
              stopOpacity="0.85"
            />
            <stop
              offset="82%"
              stopColor={color}
              stopOpacity="0.4"
            />
            <stop
              offset="100%"
              stopColor={color}
              stopOpacity="0"
            />
          </linearGradient>

          <filter
            id="medhaWaveBlur"
            x="-20%"
            y="-100%"
            width="140%"
            height="300%"
          >
            <feGaussianBlur
              stdDeviation="2.5"
              result="blur"
            />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {waves.map((wave, index) => {
          const pathA = createPath(
            index * 0.7,
            wave.amplitude,
            wave.frequency,
          );

          const pathB = createPath(
            Math.PI + index * 0.7,
            wave.amplitude,
            wave.frequency,
          );

          const pathC = createPath(
            Math.PI * 2 + index * 0.7,
            wave.amplitude,
            wave.frequency,
          );

          return (
            <motion.path
              key={index}
              d={pathA}
              fill="none"
              stroke="url(#medhaWaveGradient)"
              strokeWidth={wave.width}
              strokeLinecap="round"
              filter={
                index < 5
                  ? 'url(#medhaWaveBlur)'
                  : undefined
              }
              animate={{
                d: active
                  ? [pathA, pathB, pathC, pathA]
                  : pathA,
                opacity: active
                  ? [
                      wave.opacity * 0.65,
                      wave.opacity,
                      wave.opacity * 0.72,
                      wave.opacity * 0.65,
                    ]
                  : wave.opacity * 0.25,
              }}
              transition={{
                duration:
                  isSpeaking
                    ? duration * (0.75 + index * 0.04)
                    : duration * (1 + index * 0.05),
                repeat: active ? Infinity : 0,
                delay: wave.delay,
                ease: 'easeInOut',
              }}
            />
          );
        })}
      </svg>

      {/* central Medha sparkle */}
      <motion.div
        className="absolute left-1/2 top-1/2 z-20 flex h-10 w-10 -translate-x-1/2 -translate-y-1/2 items-center justify-center"
        animate={{
          scale: active
            ? [1, isSpeaking ? 1.16 : 1.06, 1]
            : 1,
          filter: active
            ? [
                `drop-shadow(0 0 8px ${color})`,
                `drop-shadow(0 0 24px ${color})`,
                `drop-shadow(0 0 8px ${color})`,
              ]
            : 'drop-shadow(0 0 5px rgba(255,255,255,.1))',
        }}
        transition={{
          duration: isSpeaking ? 0.85 : 1.8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      >
        <span className="text-3xl font-semibold text-white">
          ✦
        </span>
      </motion.div>

      {/* tiny moving particles */}
      {active && (
        <>
          <motion.span
            className="absolute left-[12%] top-[42%] h-1 w-1 rounded-full"
            style={{
              backgroundColor: color,
              boxShadow: `0 0 12px ${color}`,
            }}
            animate={{
              x: ['0vw', '75vw'],
              opacity: [0, 1, 0],
            }}
            transition={{
              duration: isSpeaking ? 1.2 : 2.8,
              repeat: Infinity,
              ease: 'linear',
            }}
          />

          <motion.span
            className="absolute left-[30%] top-[61%] h-[3px] w-[3px] rounded-full"
            style={{
              backgroundColor: secondaryColor,
              boxShadow: `0 0 10px ${secondaryColor}`,
            }}
            animate={{
              x: ['0vw', '55vw'],
              opacity: [0, 0.8, 0],
            }}
            transition={{
              duration: isSpeaking ? 1.5 : 3.2,
              repeat: Infinity,
              delay: 0.4,
              ease: 'linear',
            }}
          />

          <motion.span
            className="absolute left-[58%] top-[34%] h-[3px] w-[3px] rounded-full"
            style={{
              backgroundColor: '#fff',
              boxShadow: `0 0 10px ${color}`,
            }}
            animate={{
              x: ['0vw', '30vw'],
              opacity: [0, 0.75, 0],
            }}
            transition={{
              duration: isSpeaking ? 1.3 : 2.7,
              repeat: Infinity,
              delay: 0.7,
              ease: 'linear',
            }}
          />
        </>
      )}
    </div>
  );
}

/* =========================================================
   STATUS
   ========================================================= */

function StatusIndicator({
  state,
}: {
  state: string;
}) {
  let label = 'READY';
  let description = 'Ready to learn';
  let color = '#71717a';

  if (state === 'speaking') {
    label = 'SPEAKING';
    description = 'Medha is responding';
    color = '#a855f7';
  } else if (state === 'listening') {
    label = 'LISTENING';
    description = 'Go ahead, I’m listening';
    color = '#22d3ee';
  } else if (state === 'thinking') {
    label = 'THINKING';
    description = 'Preparing your answer';
    color = '#f59e0b';
  } else if (state === 'initializing') {
    label = 'CONNECTING';
    description = 'Getting Medha ready';
    color = '#60a5fa';
  }

  const active =
    state === 'speaking' ||
    state === 'listening' ||
    state === 'thinking' ||
    state === 'initializing';

  return (
    <div className="relative z-30 flex flex-col items-center">
      <motion.div
        layout
        className="flex items-center gap-2"
      >
        <motion.span
          className="h-2 w-2 rounded-full"
          style={{
            backgroundColor: color,
          }}
          animate={{
            scale: active
              ? [1, 1.5, 1]
              : 1,
            opacity: active
              ? [0.55, 1, 0.55]
              : 0.65,
          }}
          transition={{
            duration: active ? 1 : 2,
            repeat: active
              ? Infinity
              : 0,
            ease: 'easeInOut',
          }}
        />

        <AnimatePresence mode="wait">
          <motion.span
            key={label}
            initial={{
              opacity: 0,
              y: 4,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            exit={{
              opacity: 0,
              y: -4,
            }}
            className="text-xs font-medium tracking-[0.18em]"
            style={{
              color,
            }}
          >
            {label}
          </motion.span>
        </AnimatePresence>
      </motion.div>

      <AnimatePresence mode="wait">
        <motion.p
          key={description}
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          exit={{
            opacity: 0,
          }}
          className="mt-1.5 text-sm text-white/45"
        >
          {description}
        </motion.p>
      </AnimatePresence>
    </div>
  );
}

/* =========================================================
   PROPS
   ========================================================= */

export interface AgentSessionView_01Props {
  preConnectMessage?: string;
  supportsChatInput?: boolean;
  supportsVideoInput?: boolean;
  supportsScreenShare?: boolean;
  isPreConnectBufferEnabled?: boolean;

  audioVisualizerType?:
    | 'bar'
    | 'wave'
    | 'grid'
    | 'radial'
    | 'aura';

  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  className?: string;
}

/* =========================================================
   MAIN VIEW
   ========================================================= */

export function AgentSessionView_01({
  preConnectMessage = 'Start a conversation with Medha',

  supportsChatInput = true,
  supportsVideoInput = true,
  supportsScreenShare = true,

  isPreConnectBufferEnabled = true,

  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,

  ref,
  className,
  ...props
}: React.ComponentProps<'section'> &
  AgentSessionView_01Props) {
  const session = useSessionContext();

  const { messages } =
    useSessionMessages(session);

  const { state: agentState } =
    useAgent();

  const [chatOpen, setChatOpen] =
    useState(true);

  const [hasConnected, setHasConnected] =
    useState(false);

  useEffect(() => {
    if (session.isConnected) {
      setHasConnected(true);
    }
  }, [session.isConnected]);

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  const hasMessages =
    messages.length > 0;

  return (
    <section
      ref={ref}
      className={cn(
        'relative z-10 h-full w-full overflow-hidden bg-[#050508] text-white',
        className,
      )}
      {...props}
    >
      {/* =====================================================
          CLEAN BACKGROUND

          NO GRID.
          NO RECTANGLE.
          NO CHAT PANEL.
      ===================================================== */}

      <div className="pointer-events-none absolute inset-0">
        <motion.div
          className="absolute left-1/2 top-[14%] h-[360px] w-[800px] -translate-x-1/2 rounded-full blur-[140px]"
          style={{
            background:
              'radial-gradient(circle, rgba(139,92,246,.22), rgba(236,72,153,.12) 32%, rgba(37,99,235,.12) 58%, transparent 75%)',
          }}
          animate={{
            opacity:
              agentState === 'speaking'
                ? [0.45, 0.8, 0.45]
                : [0.3, 0.42, 0.3],
          }}
          transition={{
            duration:
              agentState === 'speaking'
                ? 1.2
                : 3.5,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />

        <div className="absolute inset-x-0 bottom-0 h-72 bg-linear-to-t from-[#050508] via-[#050508]/80 to-transparent" />
      </div>

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="absolute inset-x-0 top-0 z-50 flex items-start justify-between px-6 py-6 md:px-12">
        <div>
          <div className="flex items-center gap-2.5">
            <motion.span
              className="text-2xl text-violet-400"
              animate={{
                opacity: [0.65, 1, 0.65],
                scale: [1, 1.08, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
              }}
            >
              ✦
            </motion.span>

            <div>
              <h1 className="text-lg font-semibold tracking-tight">
                Medha AI
              </h1>

              <p className="text-[11px] text-white/35">
                Your AI learning companion
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-white/55">
          <span className="text-lg text-violet-400">
            ♧
          </span>

          <span>Memory Active</span>

          <motion.span
            className="h-2 w-2 rounded-full bg-emerald-400"
            animate={{
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 1.8,
              repeat: Infinity,
            }}
          />
        </div>
      </header>

      {/* =====================================================
          SONIC VISUAL
      ===================================================== */}

      <div className="absolute inset-x-0 top-[76px] z-30 flex flex-col items-center">
        <SonicWave state={agentState} />

        <StatusIndicator
          state={agentState}
        />

        {isPreConnectBufferEnabled &&
          !hasConnected &&
          !hasMessages && (
            <motion.p
              initial={{
                opacity: 0,
              }}
              animate={{
                opacity: 1,
              }}
              className="mt-5 text-xs text-white/25"
            >
              {preConnectMessage}
            </motion.p>
          )}
      </div>

      {/* =====================================================
          CHAT

          IMPORTANT:
          No surrounding rectangle/card.
          Messages sit directly on the background.
      ===================================================== */}

      <AnimatePresence>
        {chatOpen && (
          <motion.div
            initial={{
              opacity: 0,
              y: 12,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            exit={{
              opacity: 0,
              y: 12,
            }}
            transition={{
              duration: 0.35,
              ease: 'easeOut',
            }}
            className="absolute inset-x-0 bottom-[145px] top-[315px] z-20 px-5 md:bottom-[175px] md:px-12"
          >
            <div className="mx-auto h-full w-full max-w-5xl">
              {hasMessages ? (
                <AgentChatTranscript
                  agentState={agentState}
                  messages={messages}
                  className={cn(
                    'h-full w-full',

                    /* completely transparent transcript surface */
                    '[&>div]:bg-transparent',
                    '[&>div]:border-0',
                    '[&>div]:shadow-none',

                    /* message rows stay transparent */
                    '[&>div>div]:bg-transparent',
                    '[&>div>div]:border-0',
                    '[&>div>div]:shadow-none',

                    /* DYNAMIC USER BUBBLE:
                       width follows the actual message content */
                    '[&_.is-user]:flex',
                    '[&_.is-user]:justify-end',
                    '[&_.is-user>div]:w-fit',
                    '[&_.is-user>div]:max-w-[78%]',
                    '[&_.is-user>div]:ml-auto',
                    '[&_.is-user>div]:rounded-[22px]',
                    '[&_.is-user>div]:border',
                    '[&_.is-user>div]:border-violet-400/10',
                    '[&_.is-user>div]:bg-violet-500/[0.07]',
                    '[&_.is-user>div]:px-5',
                    '[&_.is-user>div]:py-3',
                    '[&_.is-user>div]:shadow-none',

                    /* DYNAMIC ASSISTANT MESSAGE:
                       no enclosing card; width follows content */
                    '[&_.is-assistant]:flex',
                    '[&_.is-assistant]:justify-start',
                    '[&_.is-assistant>div]:w-fit',
                    '[&_.is-assistant>div]:max-w-[78%]',
                    '[&_.is-assistant>div]:mr-auto',
                    '[&_.is-assistant>div]:rounded-none',
                    '[&_.is-assistant>div]:border-0',
                    '[&_.is-assistant>div]:bg-transparent',
                    '[&_.is-assistant>div]:px-0',
                    '[&_.is-assistant>div]:py-1',
                    '[&_.is-assistant>div]:shadow-none',

                    /* remove generic padding that was making large panels */
                    '[&>div>div]:px-0',
                    '[&>div>div]:py-1',
                    'md:[&>div>div]:px-0',
                  )}
                />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <motion.div
                    animate={{
                      opacity: [0.15, 0.35, 0.15],
                      y: [0, -5, 0],
                    }}
                    transition={{
                      duration: 2.5,
                      repeat: Infinity,
                      ease: 'easeInOut',
                    }}
                    className="text-center"
                  >
                    <div className="mb-3 text-3xl text-violet-400/40">
                      ✦
                    </div>

                    <p className="text-sm text-white/25">
                      Start talking with Medha
                    </p>
                  </motion.div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* =====================================================
          LIVEKIT TILE LAYOUT

          Kept mounted for camera/screen sharing,
          but hidden visually so it doesn't compete
          with the custom sonic interface.
      ===================================================== */}

      <div className="pointer-events-none absolute inset-0 z-0 opacity-[0.001]">
        <TileLayout
          chatOpen={chatOpen}
          audioVisualizerType={
            audioVisualizerType
          }
          audioVisualizerColor={
            audioVisualizerColor
          }
          audioVisualizerColorShift={
            audioVisualizerColorShift
          }
          audioVisualizerBarCount={
            audioVisualizerBarCount
          }
          audioVisualizerRadialBarCount={
            audioVisualizerRadialBarCount
          }
          audioVisualizerRadialRadius={
            audioVisualizerRadialRadius
          }
          audioVisualizerGridRowCount={
            audioVisualizerGridRowCount
          }
          audioVisualizerGridColumnCount={
            audioVisualizerGridColumnCount
          }
          audioVisualizerWaveLineWidth={
            audioVisualizerWaveLineWidth
          }
        />
      </div>

      {/* =====================================================
          BOTTOM CONTROLS
      ===================================================== */}

      <motion.div
        initial={{
          opacity: 0,
          y: 25,
        }}
        animate={{
          opacity: 1,
          y: 0,
        }}
        transition={{
          duration: 0.45,
          ease: 'easeOut',
        }}
        className="absolute inset-x-0 bottom-0 z-50 px-4 pb-4 md:px-10 md:pb-6"
      >
        <div className="mx-auto max-w-3xl">
          {/* subtle glow, not a rectangle */}
          <div className="pointer-events-none absolute bottom-0 left-1/2 h-24 w-[420px] -translate-x-1/2 rounded-full bg-violet-600/[0.06] blur-[70px]" />

          <AgentControlBar
            variant="livekit"
            controls={controls}
            isChatOpen={chatOpen}
            isConnected={
              session.isConnected
            }
            onDisconnect={
              session.end
            }
            onIsChatOpenChange={
              setChatOpen
            }
          />
        </div>
      </motion.div>
    </section>
  );
}