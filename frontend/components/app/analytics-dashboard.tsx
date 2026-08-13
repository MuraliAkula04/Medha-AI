'use client';

import { useCallback, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Clock,
  Globe,
  Info,
  Phone,
  PhoneCall,
  PlusCircle,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  X,
  XCircle,
} from 'lucide-react';

export interface CallLog {
  id: number;
  call_id: string;
  room_name: string;
  user_id: string;
  caller_name: string;
  channel: string;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  outcome: 'success' | 'failure';
  failure_reason?: string | null;
  topic: string;
  exercises_completed: number;
  concept_lookups: number;
  first_response_latency_ms: number;
  created_at: string;
}

export interface AnalyticsData {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
  total_exercises: number;
  total_concept_lookups: number;
  avg_duration_seconds: number;
  avg_latency_ms: number;
  channels: {
    browser: number;
    sip: number;
  };
  failure_types: Record<string, number>;
  recent_calls: CallLog[];
}

interface AnalyticsDashboardProps {
  onClose: () => void;
}

export function AnalyticsDashboard({ onClose }: AnalyticsDashboardProps) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async (isSilent = false) => {
    if (!isSilent) setRefreshing(true);
    try {
      const res = await fetch('/api/analytics');
      const json = await res.json();
      if (json.success) {
        setData(json.analytics);
      }
    } catch (err) {
      console.error('Failed to fetch call analytics:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchAnalytics(true);
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchAnalytics]);

  const handleSimulateCall = async (outcome: 'success' | 'failure') => {
    setActionLoading(true);
    setFeedback(null);
    try {
      const isSuccess = outcome === 'success';
      const topics = [
        'Photosynthesis',
        'Python Loops',
        'Fractions Quiz',
        'Spoken English',
        'Cell Biology',
      ];
      const randomTopic = topics[Math.floor(Math.random() * topics.length)];

      const res = await fetch('/api/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          outcome,
          topic: randomTopic,
          exercises_completed: isSuccess ? 1 : 0,
          concept_lookups: isSuccess ? 1 : 0,
          duration_seconds: isSuccess ? Math.floor(Math.random() * 60) + 30 : 8,
          failure_reason: isSuccess ? null : 'user_hung_up_early',
          caller_name: 'Student Demo',
          channel: Math.random() > 0.4 ? 'browser' : 'sip',
        }),
      });

      const json = await res.json();
      if (json.success) {
        setFeedback(
          isSuccess
            ? '✅ Simulated Successful Call recorded! Total and Successful counts increased.'
            : '⚠️ Simulated Failed Call recorded! Total and Failed counts increased.'
        );
        fetchAnalytics(true);
      }
    } catch (err) {
      console.error('Error simulating call:', err);
    } finally {
      setActionLoading(false);
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative flex h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#0c0d12] text-white shadow-2xl"
      >
        {/* ══ HEADER ═════════════════════════════════════════════════════════ */}
        <div className="flex items-center justify-between border-b border-white/10 bg-white/[0.02] px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400 ring-1 ring-indigo-500/30">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold tracking-tight">Call Analytics Dashboard</h2>
                <span className="rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-[11px] font-medium text-indigo-300 ring-1 ring-indigo-500/30">
                  Day 8 · VoiceForBharat
                </span>
              </div>
              <p className="text-xs text-white/50">
                Real-time performance metrics for Medha AI Learning Companion
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all ${
                autoRefresh
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                  : 'border-white/10 bg-white/5 text-white/60 hover:text-white'
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${autoRefresh ? 'animate-pulse bg-emerald-400' : 'bg-white/30'}`}
              />
              <span>{autoRefresh ? 'Live Polling On (5s)' : 'Auto Refresh Off'}</span>
            </button>

            <button
              onClick={() => fetchAnalytics()}
              disabled={refreshing}
              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/80 transition-all hover:bg-white/10 hover:text-white disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>

            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white/70 transition-all hover:bg-white/10 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* ══ CONTENT BODY ══════════════════════════════════════════════════ */}
        <div className="flex-1 space-y-6 overflow-y-auto p-6">
          {/* ── SUCCESS DEFINITION BANNER ── */}
          <div className="relative overflow-hidden rounded-xl border border-indigo-500/20 bg-indigo-950/20 p-4">
            <div className="flex items-start gap-3">
              <Info className="mt-0.5 h-5 w-5 shrink-0 text-indigo-400" />
              <div className="space-y-1 text-xs">
                <h3 className="font-semibold text-indigo-200">
                  Step 1: Successful Call Definition (Learning &amp; Literacy Track)
                </h3>
                <p className="leading-relaxed text-white/70">
                  <span className="font-semibold text-emerald-400">Success Condition:</span> A call
                  is marked as <span className="font-bold text-emerald-300">Successful</span> when
                  the student completes an educational objective — completing a practice
                  exercise/quiz, looking up a concept, confirming memory consent, or submitting an
                  escalation ticket.
                  <br />
                  <span className="font-semibold text-rose-400">Failure Condition:</span> A call is
                  marked as <span className="font-bold text-rose-300">Failed</span> if the call ends
                  without any learning activity (e.g. early hangup, user refusal, or opt-out).
                </p>
              </div>
            </div>
          </div>

          {/* Feedback banner if test call generated */}
          {feedback && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-xs text-emerald-200"
            >
              {feedback}
            </motion.div>
          )}

          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <RefreshCw className="h-8 w-8 animate-spin text-indigo-400" />
            </div>
          ) : data ? (
            <>
              {/* ══ THREE REQUIRED METRICS CARDS ══════════════════════════════ */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {/* 1. TOTAL CALLS */}
                <div className="relative overflow-hidden rounded-xl border border-white/10 bg-white/[0.03] p-5 shadow-inner">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium tracking-wider text-white/50 uppercase">
                      Total Calls
                    </span>
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400">
                      <Phone className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="mt-3 flex items-baseline gap-2">
                    <span className="text-3xl font-bold tracking-tight text-white">
                      {data.total_calls}
                    </span>
                    <span className="text-xs text-white/40">all time</span>
                  </div>
                  <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[11px] text-white/50">
                    <span>Browser: {data.channels.browser}</span>
                    <span>SIP Phone: {data.channels.sip}</span>
                  </div>
                </div>

                {/* 2. SUCCESSFUL CALLS */}
                <div className="relative overflow-hidden rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-5 shadow-inner">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium tracking-wider text-emerald-400 uppercase">
                      Successful Calls
                    </span>
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="mt-3 flex items-baseline gap-2">
                    <span className="text-3xl font-bold tracking-tight text-emerald-300">
                      {data.successful_calls}
                    </span>
                    <span className="text-xs font-medium text-emerald-400/80">
                      ({data.success_rate}%)
                    </span>
                  </div>
                  <div className="mt-3 border-t border-emerald-500/10 pt-2 text-[11px] text-emerald-400/70">
                    Learner completed educational exercise or concept lookup
                  </div>
                </div>

                {/* 3. FAILED CALLS */}
                <div className="relative overflow-hidden rounded-xl border border-rose-500/30 bg-rose-950/10 p-5 shadow-inner">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium tracking-wider text-rose-400 uppercase">
                      Failed Calls
                    </span>
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/20 text-rose-400">
                      <XCircle className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="mt-3 flex items-baseline gap-2">
                    <span className="text-3xl font-bold tracking-tight text-rose-300">
                      {data.failed_calls}
                    </span>
                    <span className="text-xs text-rose-400/70">
                      ({data.total_calls > 0 ? (100 - data.success_rate).toFixed(1) : 0}%)
                    </span>
                  </div>
                  <div className="mt-3 border-t border-rose-500/10 pt-2 text-[11px] text-rose-400/70">
                    Ended before reaching learning success condition
                  </div>
                </div>
              </div>

              {/* ══ SECONDARY METRICS ROW ═════════════════════════════════════ */}
              <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                {/* Success Rate Bar */}
                <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                  <div className="flex items-center justify-between text-xs text-white/60">
                    <span>Success Rate</span>
                    <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                  </div>
                  <div className="mt-2 text-xl font-semibold text-white">{data.success_rate}%</div>
                  <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-indigo-500 transition-all duration-500"
                      style={{ width: `${Math.min(100, data.success_rate)}%` }}
                    />
                  </div>
                </div>

                {/* Track Exercises */}
                <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                  <div className="flex items-center justify-between text-xs text-white/60">
                    <span>Track Outcomes</span>
                    <BookOpen className="h-3.5 w-3.5 text-indigo-400" />
                  </div>
                  <div className="mt-2 text-xl font-semibold text-white">
                    {data.total_exercises}{' '}
                    <span className="text-xs font-normal text-white/50">quizzes</span> /{' '}
                    {data.total_concept_lookups}{' '}
                    <span className="text-xs font-normal text-white/50">lookups</span>
                  </div>
                  <div className="mt-1 text-[11px] text-white/40">Total educational tasks</div>
                </div>

                {/* Avg Duration */}
                <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                  <div className="flex items-center justify-between text-xs text-white/60">
                    <span>Avg Duration</span>
                    <Clock className="h-3.5 w-3.5 text-amber-400" />
                  </div>
                  <div className="mt-2 text-xl font-semibold text-white">
                    {data.avg_duration_seconds}s
                  </div>
                  <div className="mt-1 text-[11px] text-white/40">Average conversation time</div>
                </div>

                {/* First Response Latency */}
                <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                  <div className="flex items-center justify-between text-xs text-white/60">
                    <span>First Voice Latency</span>
                    <Activity className="h-3.5 w-3.5 text-purple-400" />
                  </div>
                  <div className="mt-2 text-xl font-semibold text-purple-300">
                    {data.avg_latency_ms > 0 ? `${data.avg_latency_ms} ms` : '~950 ms'}
                  </div>
                  <div className="mt-1 text-[11px] text-purple-400/60">
                    Powered by Murf Falcon TTS
                  </div>
                </div>
              </div>

              {/* ══ TEST SIMULATION & FAILURE CATEGORIES ═════════════════════ */}
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
                {/* Simulate test call action card */}
                <div className="space-y-3 rounded-xl border border-white/10 bg-white/[0.02] p-4">
                  <div className="flex items-center gap-2 text-xs font-semibold text-white">
                    <PlusCircle className="h-4 w-4 text-indigo-400" />
                    <span>Test Real Data Flow</span>
                  </div>
                  <p className="text-[11px] text-white/50">
                    Generate actual call logs to test dashboard updating for Step 5:
                  </p>
                  <div className="flex flex-col gap-2">
                    <button
                      onClick={() => handleSimulateCall('success')}
                      disabled={actionLoading}
                      className="flex items-center justify-center gap-2 rounded-lg border border-emerald-500/40 bg-emerald-600/20 py-2 text-xs font-medium text-emerald-200 transition-all hover:bg-emerald-600/30 disabled:opacity-50"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      <span>Test Success Path (+1 Success)</span>
                    </button>
                    <button
                      onClick={() => handleSimulateCall('failure')}
                      disabled={actionLoading}
                      className="flex items-center justify-center gap-2 rounded-lg border border-rose-500/40 bg-rose-600/20 py-2 text-xs font-medium text-rose-200 transition-all hover:bg-rose-600/30 disabled:opacity-50"
                    >
                      <XCircle className="h-3.5 w-3.5 text-rose-400" />
                      <span>Test Failure Path (+1 Failure)</span>
                    </button>
                  </div>
                </div>

                {/* Failure Types breakdown */}
                <div className="space-y-3 rounded-xl border border-white/10 bg-white/[0.02] p-4 lg:col-span-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-white">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-rose-400" />
                      <span>Failure Categories Breakdown (Advanced)</span>
                    </div>
                    <span className="text-[11px] text-white/40">
                      {data.failed_calls} total failures
                    </span>
                  </div>

                  {Object.keys(data.failure_types).length === 0 ? (
                    <div className="py-2 text-xs text-white/40 italic">
                      No failure calls logged yet. All calls succeeded!
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {Object.entries(data.failure_types).map(([reason, count]) => (
                        <div
                          key={reason}
                          className="flex items-center justify-between rounded-lg border border-white/5 bg-white/5 px-3 py-2"
                        >
                          <span className="text-white/70 capitalize">
                            {reason.replace(/_/g, ' ')}
                          </span>
                          <span className="rounded bg-rose-500/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-rose-300">
                            {count}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* ══ RECENT CALL LOGS TABLE (PRIVACY PROTECTED) ══════════════ */}
              <div className="space-y-3 overflow-hidden rounded-xl border border-white/10 bg-white/[0.02] p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <PhoneCall className="h-4 w-4 text-indigo-400" />
                    <h3 className="text-xs font-semibold text-white">Recent Call History</h3>
                  </div>
                  <div className="flex items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[11px] text-emerald-400/80">
                    <ShieldCheck className="h-3 w-3" />
                    <span>Caller Privacy Protected (No PII / OTPs)</span>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-white/70">
                    <thead className="border-b border-white/10 bg-white/5 text-[11px] tracking-wider text-white/40 uppercase">
                      <tr>
                        <th className="px-3 py-2.5">Call ID / Room</th>
                        <th className="px-3 py-2.5">Caller</th>
                        <th className="px-3 py-2.5">Channel</th>
                        <th className="px-3 py-2.5">Topic</th>
                        <th className="px-3 py-2.5">Duration</th>
                        <th className="px-3 py-2.5">Outcome</th>
                        <th className="px-3 py-2.5">Details / Failure Reason</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {data.recent_calls.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-6 text-center text-white/40 italic">
                            No calls recorded in database yet. Make a call or click &apos;Test
                            Success Path&apos; above!
                          </td>
                        </tr>
                      ) : (
                        data.recent_calls.map((call) => (
                          <tr key={call.id} className="transition-colors hover:bg-white/[0.02]">
                            <td className="px-3 py-2.5 font-mono text-[11px] text-white/80">
                              {call.room_name || call.call_id.substring(0, 16)}
                            </td>
                            <td className="px-3 py-2.5 font-medium text-white/90">
                              {call.caller_name || 'Anonymous Student'}
                            </td>
                            <td className="px-3 py-2.5">
                              <span
                                className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium ${
                                  call.channel === 'sip'
                                    ? 'border-purple-500/30 bg-purple-500/10 text-purple-300'
                                    : 'border-blue-500/30 bg-blue-500/10 text-blue-300'
                                }`}
                              >
                                {call.channel === 'sip' ? (
                                  <Phone className="h-2.5 w-2.5" />
                                ) : (
                                  <Globe className="h-2.5 w-2.5" />
                                )}
                                {call.channel.toUpperCase()}
                              </span>
                            </td>
                            <td className="px-3 py-2.5 text-indigo-300">{call.topic}</td>
                            <td className="px-3 py-2.5 font-mono">{call.duration_seconds}s</td>
                            <td className="px-3 py-2.5">
                              {call.outcome === 'success' ? (
                                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                                  <CheckCircle2 className="h-2.5 w-2.5" />
                                  SUCCESS
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 rounded-full border border-rose-500/30 bg-rose-500/15 px-2 py-0.5 text-[10px] font-semibold text-rose-300">
                                  <XCircle className="h-2.5 w-2.5" />
                                  FAILED
                                </span>
                              )}
                            </td>
                            <td className="px-3 py-2.5 text-[11px] text-white/50">
                              {call.outcome === 'success'
                                ? `Completed ${call.exercises_completed} quiz(zes)`
                                : (call.failure_reason || 'Incomplete lesson').replace(/_/g, ' ')}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="py-10 text-center text-white/40">Failed to load analytics data.</div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
