'use client';

import { BookOpen, Brain, Languages, Mic, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div
      ref={ref}
      className="relative flex min-h-screen w-full overflow-hidden bg-[#09090b] text-white"
    >
      {/* Ambient background */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute top-[-15%] left-[20%] h-[500px] w-[500px] rounded-full bg-indigo-600/10 blur-[140px]" />
        <div className="absolute top-[20%] right-[-10%] h-[450px] w-[450px] rounded-full bg-violet-600/10 blur-[140px]" />
        <div className="absolute bottom-[-20%] left-[35%] h-[400px] w-[400px] rounded-full bg-blue-600/10 blur-[140px]" />
      </div>

      {/* Header */}
      <header className="absolute top-0 right-0 left-0 z-20 flex h-16 items-center justify-between border-b border-white/[0.06] px-5 md:px-8">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
            <Sparkles className="h-4 w-4 text-white" />
          </div>

          <div>
            <div className="text-sm font-semibold tracking-tight">Medha AI</div>
            <div className="text-[10px] text-zinc-500">Voice Learning Companion</div>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3 py-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
          <span className="text-xs text-zinc-400">Ready</span>
        </div>
      </header>

      {/* Main */}
      <main className="relative z-10 mx-auto flex w-full max-w-4xl flex-1 flex-col items-center justify-center px-5 pt-24 pb-20">
        {/* Brand mark */}
        <div className="mb-7 flex h-16 w-16 items-center justify-center rounded-2xl border border-white/[0.08] bg-white/[0.04] shadow-2xl shadow-indigo-950/40">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600">
            <Sparkles className="h-5 w-5" />
          </div>
        </div>

        {/* Heading */}
        <div className="text-center">
          <h1 className="text-4xl font-semibold tracking-[-0.04em] text-white md:text-5xl">
            What would you like to learn?
          </h1>

          <p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-zinc-400 md:text-base">
            Talk naturally with Medha AI. Ask questions, understand concepts, practice English, or
            explore something new.
          </p>
        </div>

        {/* Start button */}
        <Button
          size="lg"
          onClick={onStartCall}
          className="mt-9 h-12 rounded-full bg-white px-7 text-sm font-semibold text-black shadow-xl shadow-black/30 transition-all duration-200 hover:scale-[1.02] hover:bg-zinc-100"
        >
          <Mic className="mr-2 h-4 w-4" />
          {startButtonText || 'Start Learning'}
        </Button>

        {/* Capabilities */}
        <div className="mt-16 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-3">
          <FeatureCard
            icon={<Brain className="h-4 w-4" />}
            title="Learn"
            description="Understand difficult concepts"
          />

          <FeatureCard
            icon={<BookOpen className="h-4 w-4" />}
            title="Practice"
            description="Test yourself with questions"
          />

          <FeatureCard
            icon={<Languages className="h-4 w-4" />}
            title="Explore"
            description="Learn across languages"
          />
        </div>

        {/* Supported languages */}
        <div className="mt-8 flex items-center gap-2 text-xs text-zinc-600">
          <span>Try speaking in</span>
          <span className="text-zinc-400">English</span>
          <span>•</span>
          <span className="text-zinc-400">తెలుగు</span>
          <span>•</span>
          <span className="text-zinc-400">हिन्दी</span>
        </div>
      </main>

      {/* Footer */}
      <footer className="absolute right-0 bottom-4 left-0 z-10 text-center">
        <p className="text-[11px] text-zinc-600">Medha AI • Learning & Literacy</p>
      </footer>
    </div>
  );
};

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="group rounded-2xl border border-white/[0.07] bg-white/[0.025] p-4 text-left transition-all duration-200 hover:border-white/[0.12] hover:bg-white/[0.04]">
      <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg bg-white/[0.06] text-zinc-300">
        {icon}
      </div>

      <div className="text-sm font-medium text-zinc-200">{title}</div>

      <div className="mt-1 text-xs leading-5 text-zinc-500">{description}</div>
    </div>
  );
}
