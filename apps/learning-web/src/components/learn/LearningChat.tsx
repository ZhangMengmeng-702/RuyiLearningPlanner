import React, { useRef, useEffect } from 'react';
import type { ChatMessage as ChatMessageType } from '../../types';
import { ChatMessage as ChatMessageCmp } from './ChatMessage';

interface Props {
  messages: ChatMessageType[];
  loading: boolean;
}

export const LearningChat: React.FC<Props> = ({ messages, loading }) => {
  const msgEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    msgEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg, i) => (
        <ChatMessageCmp key={i} message={msg} />
      ))}
      {loading && (
        <div className="flex justify-start">
          <div className="bg-gray-800 text-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
            <div className="flex space-x-1.5">
              <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.1s]" />
              <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.2s]" />
            </div>
          </div>
        </div>
      )}
      <div ref={msgEndRef} />
    </div>
  );
};