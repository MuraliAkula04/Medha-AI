'use client';

import { type ComponentProps } from 'react';
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

export function AgentChatTranscript({
  agentState,
  messages = [],
  className,
  ...props
}: AgentChatTranscriptProps) {
  return (
    <Conversation className={className} {...props}>
      <ConversationContent className="mx-auto w-full max-w-3xl space-y-7 px-4 py-8 md:px-6">
        {messages.map((receivedMessage) => {
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
                className={`flex max-w-[88%] items-end gap-3 md:max-w-[76%] ${
                  isUser ? 'flex-row-reverse' : 'flex-row'
                }`}
              >
                {/* Avatar */}
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
                    isUser
                      ? 'border border-white/10 bg-white/[0.07] text-white/70'
                      : 'bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/20'
                  }`}
                >
                  {isUser ? 'You' : 'M'}
                </div>

                <div className="min-w-0">
                  {/* Speaker */}
                  <div
                    className={`mb-1.5 px-1 text-[11px] font-medium tracking-wide text-white/40 ${
                      isUser ? 'text-right' : 'text-left'
                    }`}
                  >
                    {isUser ? 'You' : 'Medha AI'}
                  </div>

                  {/* Bubble */}
                  <MessageContent
                    className={`rounded-2xl px-4 py-3 text-sm leading-6 md:text-[15px] ${
                      isUser
                        ? 'rounded-br-md bg-white/[0.08] text-white'
                        : 'rounded-bl-md border border-white/[0.07] bg-white/[0.035] text-white/90'
                    }`}
                  >
                    <MessageResponse>{message}</MessageResponse>
                  </MessageContent>

                  {/* Timestamp */}
                  <div
                    className={`mt-1.5 px-1 text-[10px] text-white/25 ${
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

        {/* Thinking */}
        <AnimatePresence>
          {agentState === 'thinking' && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-[11px] font-semibold text-white">
                M
              </div>

              <div>
                <div className="mb-1.5 text-[11px] font-medium text-white/40">Medha AI</div>

                <div className="rounded-2xl rounded-bl-md border border-white/[0.07] bg-white/[0.035] px-4 py-3">
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
