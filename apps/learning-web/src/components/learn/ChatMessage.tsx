import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { useNavigate } from 'react-router-dom';
import type { ChatMessage as ChatMessageType } from '../../types';

interface Props {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<Props> = ({ message }) => {
  const isUser = message.role === 'user';
  const navigate = useNavigate();
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!contentRef.current || isUser) return;
    const container = contentRef.current;
    const links = container.querySelectorAll('a[href^="/"]');

    const handleClick = (e: Event) => {
      const target = e.currentTarget as HTMLAnchorElement;
      const href = target.getAttribute('href');
      if (href && href.startsWith('/')) {
        e.preventDefault();
        navigate(href);
      }
    };

    links.forEach(link => {
      link.addEventListener('click', handleClick);
    });

    return () => {
      links.forEach(link => {
        link.removeEventListener('click', handleClick);
      });
    };
  }, [message.content, isUser, navigate]);

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
        isUser
          ? 'bg-indigo-600 text-white rounded-br-md'
          : 'bg-gray-800 text-gray-100 rounded-bl-md'
      }`}>
        {isUser ? (
          <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        ) : (
          <div ref={contentRef} className="prose prose-invert prose-sm max-w-none
            [&_a]:text-indigo-400 [&_a]:underline [&_a]:underline-offset-2
            [&_code]:bg-gray-700 [&_code]:px-1 [&_code]:rounded
            [&_pre]:bg-gray-900 [&_pre]:p-3 [&_pre]:rounded-lg
            [&_ul]:list-disc [&_ul]:pl-4 [&_ol]:list-decimal [&_ol]:pl-4">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
};