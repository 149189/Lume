// @ts-nocheck
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '@root/api-client';

// Google Material 3 Color Tokens
const GOOGLE_BLUE = '#1A73E8';
const SURFACE = 'bg-white';
const SURFACE_VARIANT = 'bg-gray-50';
const ON_SURFACE = 'text-gray-800';
const ON_SURFACE_VARIANT = 'text-gray-500';

// Types
export type SenderRole = 'user' | 'assistant';
export type MessageStatus = 'sending' | 'sent' | 'delivered' | 'read' | 'error';

export interface Message {
  id: string;
  role: SenderRole;
  text: string;
  timestamp: string; // ISO
  status?: MessageStatus;
  suggestions?: string[];
  reactions?: string[]; // e.g., ['👍','✨']
}

interface ChatInterfaceProps {
  title?: string;
  placeholder?: string;
  className?: string;
  onError?: (error: string) => void;
}

const reactionSet = ['👍', '❤️', '😂', '🎉', '✨', '👀'];

// Google-style Three Dots Loader
const DotsLoader: React.FC = () => {
  return (
    <div className="flex items-center gap-1 px-3 py-2" aria-live="polite" aria-label="Loading">
      <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:-0.2s]"></span>
      <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></span>
      <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0.2s]"></span>
    </div>
  );
};

const HeaderBar: React.FC<{ title: string }>= ({ title }) => {
  return (
    <header className={`sticky top-0 z-10 ${SURFACE} border-b border-gray-100`}>
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        <div className="flex h-14 items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl" style={{ backgroundColor: GOOGLE_BLUE }} />
            <h1 className={`font-medium ${ON_SURFACE}`}>{title}</h1>
          </div>
          <nav className="flex items-center gap-2">
            <button className="px-3 py-1.5 rounded-full text-sm text-gray-600 hover:bg-gray-100 transition" aria-label="New chat">New</button>
            <button className="px-3 py-1.5 rounded-full text-sm text-gray-600 hover:bg-gray-100 transition" aria-label="Settings">Settings</button>
          </nav>
        </div>
      </div>
    </header>
  );
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  title = 'Lume',
  placeholder = 'Message Lume',
  className,
  onError,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeReactionsFor, setActiveReactionsFor] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Memo: formatted threads with day separators (optional future)
  const thread = useMemo(() => messages, [messages]);

  // Helpers
  const nowISO = () => new Date().toISOString();
  const newId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  const addMessage = (msg: Message) => setMessages(prev => [...prev, msg]);
  const updateMessage = (id: string, patch: Partial<Message>) =>
    setMessages(prev => prev.map(m => (m.id === id ? { ...m, ...patch } : m)));
  const removeMessage = (id: string) =>
    setMessages(prev => prev.filter(m => m.id !== id));

  // Copy/share/delete actions
  const copyMessage = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      // ignore
    }
  };

  const shareMessage = async (text: string) => {
    try {
      if (navigator.share) {
        await navigator.share({ text });
      } else {
        await navigator.clipboard.writeText(text);
      }
    } catch (_) {
      // ignore
    }
  };

  const toggleReaction = (id: string, emoji: string) => {
    setMessages(prev => prev.map(m => {
      if (m.id !== id) return m;
      const reactions = new Set(m.reactions || []);
      if (reactions.has(emoji)) reactions.delete(emoji); else reactions.add(emoji);
      return { ...m, reactions: Array.from(reactions) };
    }));
  };

  const handleQuickReply = (text: string) => {
    setInput(text);
    inputRef.current?.focus();
  };

  const handleSubmit = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMsgId = newId();
    addMessage({ id: userMsgId, role: 'user', text: trimmed, timestamp: nowISO(), status: 'sent' });
    setInput('');
    setIsLoading(true);

    try {
      const res = await api.sendPrompt(trimmed);
      if (res.error || !res.data) {
        throw new Error(res.error || 'Unknown error');
      }

      // Construct assistant message from backend response
      const assistantText = res.data.result?.message || res.data.message || 'Done.';
      const suggestions: string[] = generateSuggestions(res.data.intent?.service, res.data.intent?.action);

      addMessage({
        id: newId(),
        role: 'assistant',
        text: assistantText,
        timestamp: nowISO(),
        status: 'delivered',
        suggestions,
      });
    } catch (err: any) {
      const msg = err?.message || 'Failed to send message';
      onError?.(msg);
      addMessage({ id: newId(), role: 'assistant', text: `Error: ${msg}`, timestamp: nowISO(), status: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  // Enter to submit, Shift+Enter to newline
  const onKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSubmit();
    }
  };

  return (
    <div className={`flex flex-col h-full ${SURFACE} ${className ?? ''} font-sans`}>
      <HeaderBar title={title} />

      {/* Conversation */}
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-4 space-y-4">
          {thread.map((m) => (
            <MessageBubble
              key={m.id}
              message={m}
              onCopy={() => copyMessage(m.text)}
              onShare={() => shareMessage(m.text)}
              onDelete={() => removeMessage(m.id)}
              onReact={(emoji) => toggleReaction(m.id, emoji)}
              onToggleReactions={() => setActiveReactionsFor(prev => (prev === m.id ? null : m.id))}
              showReactions={activeReactionsFor === m.id}
              onQuickReply={handleQuickReply}
            />
          ))}

          {isLoading && (
            <div className="flex items-end gap-2">
              <AssistantAvatar />
              <div className="rounded-3xl bg-gray-100 text-gray-800 shadow-sm px-3 py-2">
                <DotsLoader />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </main>

      {/* Composer */}
      <footer className={`border-t border-gray-100 ${SURFACE}`}>
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-3">
          <div className="rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-gray-200 overflow-hidden">
            <div className="relative">
              {/* Floating label pattern */}
              <label className="absolute left-3 top-2 text-xs text-gray-500 pointer-events-none">Message</label>
              <textarea
                ref={inputRef}
                aria-label="Message input"
                className="w-full resize-none bg-white outline-none pt-6 pb-3 px-3 text-[15px] leading-6 placeholder-gray-400"
                placeholder={placeholder}
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
              />
              <div className="flex items-center justify-between px-2 pb-2">
                <div className="flex items-center gap-1">
                  {/* Placeholder for attachments, mic, etc. */}
                </div>
                <button
                  onClick={handleSubmit}
                  aria-label="Send message"
                  disabled={isLoading || !input.trim()}
                  className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-white shadow-sm disabled:opacity-60"
                  style={{ backgroundColor: GOOGLE_BLUE }}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor" />
                  </svg>
                  Send
                </button>
              </div>
            </div>
          </div>
          <p className={`mt-2 text-xs ${ON_SURFACE_VARIANT}`}>Press Enter to send • Shift+Enter for new line</p>
        </div>
      </footer>
    </div>
  );
};

// Assistant Avatar (Google style)
const AssistantAvatar: React.FC = () => (
  <div className="flex items-end">
    <div
      className="w-8 h-8 rounded-2xl shadow-sm"
      style={{ backgroundColor: GOOGLE_BLUE }}
      aria-hidden
    />
  </div>
);

interface MessageBubbleProps {
  message: Message;
  onCopy: () => void;
  onShare: () => void;
  onDelete: () => void;
  onReact: (emoji: string) => void;
  onToggleReactions: () => void;
  showReactions: boolean;
  onQuickReply: (text: string) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onCopy,
  onShare,
  onDelete,
  onReact,
  onToggleReactions,
  showReactions,
  onQuickReply,
}) => {
  const isUser = message.role === 'user';
  const alignment = isUser ? 'justify-end' : 'justify-start';
  const bubbleColor = isUser ? 'text-white' : 'text-gray-900';
  const bubbleBg = isUser ? '' : 'bg-gray-100';
  const bubbleStyle = isUser
    ? { backgroundColor: GOOGLE_BLUE }
    : undefined;

  return (
    <div className={`flex ${alignment} group`}>
      {!isUser && <AssistantAvatar />}

      <div className={`max-w-[85%] sm:max-w-[70%] flex flex-col ${isUser ? 'items-end' : 'items-start'} ${isUser ? 'ml-auto' : 'ml-2'} gap-1`}>
        <div
          className={`relative px-4 py-2 rounded-3xl shadow-sm ${bubbleColor} ${bubbleBg}`}
          style={bubbleStyle}
        >
          <p className="whitespace-pre-wrap break-words text-[15px] leading-6">{message.text}</p>

          {/* Actions on hover */}
          <div className="absolute -top-8 right-1 hidden group-hover:flex items-center gap-1">
            <button title="Copy" aria-label="Copy" onClick={onCopy} className="p-1 rounded-full bg-white shadow border border-gray-200 hover:bg-gray-50">
              <span className="sr-only">Copy</span>
              📋
            </button>
            <button title="Share" aria-label="Share" onClick={onShare} className="p-1 rounded-full bg-white shadow border border-gray-200 hover:bg-gray-50">🔗</button>
            <button title="Delete" aria-label="Delete" onClick={onDelete} className="p-1 rounded-full bg-white shadow border border-gray-200 hover:bg-gray-50">🗑️</button>
            <button title="React" aria-label="React" onClick={onToggleReactions} className="p-1 rounded-full bg-white shadow border border-gray-200 hover:bg-gray-50">😊</button>
          </div>
        </div>

        {/* Reactions row */}
        {showReactions && (
          <div className="flex items-center gap-1 mt-1">
            {reactionSet.map((emoji) => (
              <button
                key={emoji}
                onClick={() => onReact(emoji)}
                className="px-2 py-1 rounded-full bg-gray-100 hover:bg-gray-200 text-sm"
                aria-label={`React ${emoji}`}
              >
                {emoji}
              </button>
            ))}
          </div>
        )}

        {/* Timestamp & status */}
        <div className={`flex items-center gap-2 ${ON_SURFACE_VARIANT} text-xs px-1`}>
          <time dateTime={message.timestamp}>{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>
          {isUser && (
            <span className="inline-flex items-center gap-1">
              {message.status === 'read' && <span title="Read">✔✔</span>}
              {message.status === 'delivered' && <span title="Delivered">✔</span>}
              {message.status === 'error' && <span className="text-red-500" title="Error">⚠</span>}
            </span>
          )}
        </div>

        {/* Quick replies under assistant messages */}
        {message.role === 'assistant' && message.suggestions && message.suggestions.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-1">
            {message.suggestions.map(s => (
              <button
                key={s}
                onClick={() => onQuickReply(s)}
                className="px-3 py-1.5 rounded-full bg-gray-100 hover:bg-gray-200 text-sm transition"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Suggestion generator (simple heuristic based on intent)
function generateSuggestions(service?: string, action?: string): string[] {
  if (!service) return ['Tell me more', 'Undo', 'Help'];
  const s = service.toLowerCase();
  const a = (action || '').toLowerCase();
  if (s === 'gmail') return ['Show inbox', 'Draft a reply', 'Search email from Alex'];
  if (s === 'calendar') return ['View my week', 'Create event', 'Reschedule meeting'];
  if (s === 'tasks') return ['List tasks', 'Add a task', 'Mark task done'];
  if (s === 'keep') return ['New note', 'Search notes', 'Make a checklist'];
  if (s === 'maps') return ['Nearby cafes', 'Traffic to work', 'Best route home'];
  return ['Okay', 'Another example', 'Help'];
}

export default ChatInterface;
