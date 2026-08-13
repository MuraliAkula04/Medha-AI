'use client';

import { useMemo, type ComponentProps } from 'react';
import { AnimatePresence } from 'motion/react';
import { type AgentState, type ReceivedMessage } from '@livekit/components-react';
import { AgentChatIndicator } from '@/components/agents-ui/agent-chat-indicator';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import { Message, MessageContent, MessageResponse } from '@/components/ai-elements/message';

export interface AgentChatTranscriptProps extends ComponentProps<'div'> {
  agentState?: AgentState;
  messages?: ReceivedMessage[];
  className?: string;
}

/**
 * Combines consecutive messages from the same speaker into a single sentence/turn
 * so speech does not get fragmented into several partial messages.
 */
function groupMessages(rawMessages: ReceivedMessage[]): ReceivedMessage[] {
  if (!rawMessages || rawMessages.length === 0) return [];

  const grouped: ReceivedMessage[] = [];

  for (const msg of rawMessages) {
    if (!msg.message || !msg.message.trim()) continue;
    const last = grouped[grouped.length - 1];

    const isUser = msg.from?.isLocal === true;
    const lastIsUser = last?.from?.isLocal === true;
    const isSameSpeaker = last && isUser === lastIsUser;

    // If consecutive messages are from the same speaker within 6 seconds, merge them!
    const isRecent = last && Math.abs(msg.timestamp - last.timestamp) < 6000;

    if (isSameSpeaker && isRecent) {
      // Append new sentence segment cleanly
      const currentText = last.message.trim();
      const newText = msg.message.trim();
      // Avoid duplicate exact repeats if STT sends identical phrase
      if (!currentText.endsWith(newText)) {
        last.message = `${currentText} ${newText}`;
      }
      last.timestamp = msg.timestamp;
    } else {
      grouped.push({ ...msg });
    }
  }

  return grouped;
}

export function AgentChatTranscript({
  agentState,
  messages = [],
  className,
  ...props
}: AgentChatTranscriptProps) {
  const groupedMessages = useMemo(() => groupMessages(messages), [messages]);

  return (
    <Conversation className={className} {...props}>
      <ConversationContent className="mx-auto w-full max-w-3xl space-y-6 px-4 py-8 md:px-6">
        {groupedMessages.map((receivedMessage) => {
          const { id, timestamp, from, message } = receivedMessage;

          const isUser = from?.isLocal === true;

          const time = new Date(timestamp);

          const timeLabel = time.toLocaleTimeString(
            typeof navigator !== 'undefined' ? navigator.language : 'en-IN',
            {
              hour: '2-digit',
              minute: '2-digit',
            }
          );

          return (
            <Message
              key={id}
              title={timeLabel}
              from={isUser ? 'user' : 'assistant'}
              className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`flex max-w-[90%] items-start gap-3 md:max-w-[80%] ${
                  isUser ? 'flex-row-reverse' : 'flex-row'
                }`}
              >
                {/* Avatar */}
                <div
                  className={`mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${
                    isUser
                      ? 'border border-violet-400/30 bg-violet-500/20 text-violet-200 shadow-md shadow-violet-950/40'
                      : 'bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-500/30'
                  }`}
                >
                  {isUser ? 'You' : 'M'}
                </div>

                <div className="min-w-0 flex-1">
                  {/* Speaker */}
                  <div
                    className={`mb-1.5 px-1 text-[11px] font-semibold tracking-wide ${
                      isUser ? 'text-right text-violet-300/80' : 'text-left text-violet-400'
                    }`}
                  >
                    {isUser ? 'You' : 'Medha AI'}
                  </div>

                  {/* Bubble */}
                  <MessageContent
                    className={`rounded-2xl px-5 py-3.5 text-sm leading-relaxed md:text-[15px] ${
                      isUser
                        ? 'rounded-tr-xs border border-violet-500/35 bg-violet-600/25 text-white shadow-md shadow-violet-950/30'
                        : 'rounded-tl-xs border border-violet-500/20 bg-[#161622] text-slate-100 shadow-xl shadow-black/40'
                    }`}
                  >
                    <MessageResponse className="text-slate-100 dark:text-slate-100">
                      {message}
                    </MessageResponse>
                  </MessageContent>

                  {/* Timestamp */}
                  <div
                    className={`mt-1.5 px-1 text-[10px] text-white/30 ${
                      isUser ? 'text-right' : 'text-left'
                    }`}
                  >
                    {timeLabel}
                  </div>
                </div>
              </div>
            </Message>
          );
        })}

        {/* Thinking State */}
        <AnimatePresence>
          {agentState === 'thinking' && (
            <div className="flex items-start gap-3">
              <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 text-[11px] font-bold text-white shadow-lg shadow-violet-500/30">
                M
              </div>

              <div>
                <div className="mb-1.5 text-[11px] font-semibold text-violet-400">Medha AI</div>

                <div className="rounded-2xl rounded-tl-xs border border-violet-500/20 bg-[#161622] px-5 py-3.5 shadow-xl shadow-black/40">
                  <AgentChatIndicator size="sm" />
                </div>
              </div>
            </div>
          )}
        </AnimatePresence>
      </ConversationContent>

      <ConversationScrollButton />
    </Conversation>
  );
}
