'use client';

import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Clock,
  MessageSquare,
  PhoneCall,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  UserCheck,
  X,
} from 'lucide-react';

export interface EscalationItem {
  id?: number;
  ref_id: string;
  user_id: string;
  caller_name: string;
  reason: string;
  summary: string;
  checked_steps?: string;
  urgency: 'low' | 'medium' | 'high' | 'emergency' | string;
  language: string;
  contact_method: string;
  status: 'Open' | 'In Progress' | 'Resolved' | string;
  created_at: string;
}

interface EscalationDashboardProps {
  realtimeEscalation?: EscalationItem | null;
  onClose?: () => void;
}

export function EscalationDashboard({ realtimeEscalation, onClose }: EscalationDashboardProps) {
  const [escalations, setEscalations] = useState<EscalationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'All' | 'Open' | 'In Progress' | 'Resolved'>('All');
  const [updatingRefId, setUpdatingRefId] = useState<string | null>(null);

  const fetchEscalations = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/escalations');
      const data = await res.json();
      if (data.success && Array.isArray(data.escalations)) {
        setEscalations(data.escalations);
      }
    } catch (err) {
      console.error('Failed to fetch escalations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEscalations();
  }, []);

  // When a realtime escalation comes through LiveKit data channel, prepend it!
  useEffect(() => {
    if (realtimeEscalation) {
      setEscalations((prev) => {
        const exists = prev.some((e) => e.ref_id === realtimeEscalation.ref_id);
        if (exists) return prev;
        return [realtimeEscalation, ...prev];
      });
    }
  }, [realtimeEscalation]);

  const handleUpdateStatus = async (ref_id: string, newStatus: string) => {
    setUpdatingRefId(ref_id);
    try {
      const res = await fetch('/api/escalations', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ref_id, status: newStatus }),
      });
      const data = await res.json();
      if (data.success) {
        setEscalations((prev) =>
          prev.map((item) => (item.ref_id === ref_id ? { ...item, status: newStatus } : item))
        );
      }
    } catch (err) {
      console.error('Failed to update status:', err);
    } finally {
      setUpdatingRefId(null);
    }
  };

  const filteredEscalations = escalations.filter((item) => {
    if (activeTab === 'All') return true;
    return item.status.toLowerCase() === activeTab.toLowerCase();
  });

  const getUrgencyBadge = (urgency: string) => {
    const u = urgency.toLowerCase();
    if (u === 'emergency') {
      return (
        <span className="inline-flex animate-pulse items-center gap-1 rounded-full border border-red-500/30 bg-red-500/20 px-2.5 py-0.5 text-xs font-medium text-red-400">
          <AlertTriangle className="h-3 w-3 text-red-400" />
          Emergency
        </span>
      );
    }
    if (u === 'high') {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-orange-500/30 bg-orange-500/20 px-2.5 py-0.5 text-xs font-medium text-orange-400">
          <AlertTriangle className="h-3 w-3 text-orange-400" />
          High Urgency
        </span>
      );
    }
    if (u === 'medium') {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/20 px-2.5 py-0.5 text-xs font-medium text-amber-400">
          <Clock className="h-3 w-3 text-amber-400" />
          Medium
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-blue-500/30 bg-blue-500/20 px-2.5 py-0.5 text-xs font-medium text-blue-400">
        <Clock className="h-3 w-3 text-blue-400" />
        Low
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    if (s === 'resolved') {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/20 px-2.5 py-0.5 text-xs font-medium text-emerald-400">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
          Resolved
        </span>
      );
    }
    if (s === 'in progress') {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-purple-500/30 bg-purple-500/20 px-2.5 py-0.5 text-xs font-medium text-purple-400">
          <UserCheck className="h-3.5 w-3.5 text-purple-400" />
          In Progress
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/20 px-2.5 py-0.5 text-xs font-medium text-amber-400">
        <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
        Open
      </span>
    );
  };

  return (
    <div className="mx-auto flex max-h-[85vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/95 text-zinc-100 shadow-2xl backdrop-blur-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950/60 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-purple-500/20 bg-purple-500/10 p-2.5 text-purple-400">
            <UserCheck className="h-6 w-6" />
          </div>
          <div>
            <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tight text-white">
              Human Escalation Dashboard
              <span className="rounded-full border border-purple-500/30 bg-purple-500/20 px-2 py-0.5 text-xs text-purple-300">
                Day 7 Live
              </span>
            </h2>
            <p className="mt-0.5 text-xs text-zinc-400">
              Review & dispatch requests needing human teacher intervention (PII Scrubbed)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchEscalations}
            disabled={loading}
            className="rounded-lg border border-zinc-700/50 bg-zinc-800/60 p-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
            title="Refresh Escalations"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="rounded-lg border border-zinc-700/50 bg-zinc-800/60 p-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center justify-between border-b border-zinc-800/60 bg-zinc-900/40 px-6 py-3">
        <div className="flex items-center gap-2">
          {(['All', 'Open', 'In Progress', 'Resolved'] as const).map((tab) => {
            const count =
              tab === 'All'
                ? escalations.length
                : escalations.filter((e) => e.status.toLowerCase() === tab.toLowerCase()).length;

            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all ${
                  activeTab === tab
                    ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
                    : 'text-zinc-400 hover:bg-zinc-800/60 hover:text-white'
                }`}
              >
                {tab}
                <span
                  className={`py-0.2 rounded-md px-1.5 text-[10px] ${
                    activeTab === tab ? 'bg-purple-700 text-white' : 'bg-zinc-800 text-zinc-400'
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-1.5 rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>PII Stripped & Permission Verified</span>
        </div>
      </div>

      {/* Content Body */}
      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {loading && escalations.length === 0 ? (
          <div className="py-16 text-center text-zinc-500">
            <RefreshCw className="mx-auto mb-3 h-8 w-8 animate-spin text-purple-400" />
            <p className="text-sm">Loading human escalation requests...</p>
          </div>
        ) : filteredEscalations.length === 0 ? (
          <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-950/30 py-16 text-center text-zinc-500">
            <CheckCircle2 className="mx-auto mb-3 h-10 w-10 text-zinc-600" />
            <p className="text-sm font-medium text-zinc-400">
              No {activeTab.toLowerCase()} escalation tickets found
            </p>
            <p className="mx-auto mt-1 max-w-sm text-xs text-zinc-500">
              When Medha AI detects student distress or teacher consultation requests and obtains
              permission, new requests appear here in real-time.
            </p>
          </div>
        ) : (
          filteredEscalations.map((ticket) => (
            <div
              key={ticket.ref_id}
              className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-950/60 p-5 shadow-md transition-all hover:border-zinc-700/80 hover:shadow-xl"
            >
              {/* Ticket Top bar */}
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-md border border-purple-800/40 bg-purple-950/60 px-2 py-0.5 font-mono text-xs font-semibold text-purple-400">
                      {ticket.ref_id}
                    </span>
                    {getUrgencyBadge(ticket.urgency)}
                    {getStatusBadge(ticket.status)}
                    <span className="text-xs text-zinc-500">
                      {new Date(ticket.created_at).toLocaleString()}
                    </span>
                  </div>
                  <h3 className="mt-2 text-base font-semibold text-zinc-100">{ticket.reason}</h3>
                </div>

                {/* Status Action Buttons */}
                <div className="flex items-center gap-2">
                  {ticket.status !== 'In Progress' && ticket.status !== 'Resolved' && (
                    <button
                      onClick={() => handleUpdateStatus(ticket.ref_id, 'In Progress')}
                      disabled={updatingRefId === ticket.ref_id}
                      className="flex items-center gap-1.5 rounded-lg border border-purple-500/30 bg-purple-600/20 px-3 py-1.5 text-xs font-medium text-purple-300 transition-colors hover:bg-purple-600/40"
                    >
                      <UserCheck className="h-3.5 w-3.5" />
                      Mark In Progress
                    </button>
                  )}
                  {ticket.status !== 'Resolved' && (
                    <button
                      onClick={() => handleUpdateStatus(ticket.ref_id, 'Resolved')}
                      disabled={updatingRefId === ticket.ref_id}
                      className="flex items-center gap-1.5 rounded-lg border border-emerald-500/30 bg-emerald-600/20 px-3 py-1.5 text-xs font-medium text-emerald-300 transition-colors hover:bg-emerald-600/40"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Resolve Ticket
                    </button>
                  )}
                  {ticket.status === 'Resolved' && (
                    <button
                      onClick={() => handleUpdateStatus(ticket.ref_id, 'Open')}
                      disabled={updatingRefId === ticket.ref_id}
                      className="rounded-lg bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-400 transition-colors hover:bg-zinc-700"
                    >
                      Reopen
                    </button>
                  )}
                </div>
              </div>

              {/* Summary Box */}
              <div className="space-y-2 rounded-lg border border-zinc-800/80 bg-zinc-900/90 p-3.5">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-zinc-400">
                  <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                  Structured Problem Summary (PII Redacted)
                </div>
                <p className="text-xs leading-relaxed text-zinc-200">{ticket.summary}</p>
              </div>

              {/* Agent Checked Steps */}
              {ticket.checked_steps && (
                <div className="rounded-lg border border-zinc-800/50 bg-zinc-900/40 p-3 text-xs text-zinc-400">
                  <span className="font-medium text-zinc-300">What Agent Checked: </span>
                  {ticket.checked_steps}
                </div>
              )}

              {/* Footer Details */}
              <div className="flex items-center justify-between border-t border-zinc-800/40 pt-1 text-xs text-zinc-400">
                <div className="flex items-center gap-4">
                  <span>
                    <strong className="text-zinc-300">Student:</strong> {ticket.caller_name}
                  </span>
                  <span>
                    <strong className="text-zinc-300">Language:</strong> {ticket.language}
                  </span>
                  <span className="flex items-center gap-1">
                    <PhoneCall className="h-3 w-3 text-purple-400" />
                    <strong className="text-zinc-300">Follow-up:</strong> {ticket.contact_method}
                  </span>
                </div>

                <span className="font-mono text-[11px] text-zinc-500">
                  Caller ID: {ticket.user_id}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
