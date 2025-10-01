'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { apiClient, User, Message, SendMessageResponse } from '@/lib/api';

interface ChatInterfaceProps {
  user: User;
  conversationId: number | null;
  onConversationCreate: (id: number) => void;
  onPermissionRequest: (permissions: string[], state: string) => void;
}

export default function ChatInterface({
  user,
  conversationId,
  onConversationCreate,
  onPermissionRequest,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (conversationId) {
      loadMessages();
    } else {
      setMessages([]);
    }
  }, [conversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadMessages = async () => {
    if (!conversationId) return;
    
    setLoadingMessages(true);
    try {
      const response = await apiClient.getConversationMessages(conversationId);
      setMessages(response.messages);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoadingMessages(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || loading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setLoading(true);

    // Add user message optimistically
    const tempUserMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      const response: SendMessageResponse = await apiClient.sendMessage(
        userMessage,
        conversationId || undefined
      );

      // Update conversation ID if new
      if (!conversationId && response.conversation_id) {
        onConversationCreate(response.conversation_id);
      }

      // Check if permissions are required
      if (response.requires_permissions && response.missing_permissions) {
        // Create a state for permission request
        const state = `perm_${Date.now()}`;
        onPermissionRequest(response.missing_permissions, state);
        
        // Add assistant message about permissions
        const permMessage: Message = {
          id: Date.now() + 1,
          role: 'assistant',
          content: `I need additional permissions to help you with this request. Please grant access to: ${response.missing_permissions.join(', ')}`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev.slice(0, -1), response.user_message, permMessage]);
      } else {
        // Replace optimistic message with actual messages
        if (response.assistant_message) {
          setMessages((prev) => [
            ...prev.slice(0, -1),
            response.user_message,
            response.assistant_message!,
          ]);
        } else {
          setMessages((prev) => [...prev.slice(0, -1), response.user_message]);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic message on error
      setMessages((prev) => prev.slice(0, -1));
      
      // Show error message
      const errorMessage: Message = {
        id: Date.now(),
        role: 'system',
        content: 'Failed to send message. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-white">
      {/* Chat Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h2 className="text-xl font-semibold text-gray-800">
          {conversationId ? 'Conversation' : 'New Chat'}
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Ask me to manage your Gmail, Calendar, Tasks, or Keep
        </p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loadingMessages ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin text-google-blue mx-auto" />
              <p className="text-gray-500 mt-2">Loading messages...</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-green-100 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Send className="w-8 h-8 text-google-blue" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">Start a conversation</h3>
              <p className="text-gray-600 mb-4">
                Try asking me to send an email, create a calendar event, or manage your tasks
              </p>
              <div className="space-y-2 text-left bg-gray-50 rounded-lg p-4">
                <p className="text-sm font-medium text-gray-700">Example prompts:</p>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• "Send an email to john@example.com about the meeting"</li>
                  <li>• "Schedule a meeting for tomorrow at 2 PM"</li>
                  <li>• "Create a task to review the report"</li>
                  <li>• "Make a note about project ideas"</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} fade-in`}
              >
                <div
                  className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-google-blue text-white'
                      : message.role === 'system'
                      ? 'bg-red-50 text-red-700 border border-red-200'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <p className="message-content text-sm leading-relaxed">{message.content}</p>
                  <p
                    className={`text-xs mt-2 ${
                      message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                    }`}
                  >
                    {formatTime(message.timestamp)}
                  </p>
                  {message.detected_services && Object.values(message.detected_services).some((v) => v) && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {Object.entries(message.detected_services).map(
                        ([service, detected]) =>
                          detected && (
                            <span
                              key={service}
                              className={`text-xs px-2 py-1 rounded ${
                                message.role === 'user'
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-gray-200 text-gray-700'
                              }`}
                            >
                              {service}
                            </span>
                          )
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start fade-in">
                <div className="bg-gray-100 rounded-2xl px-4 py-3">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full loading-dot"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full loading-dot"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full loading-dot"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <form onSubmit={handleSendMessage} className="flex items-center space-x-3">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={loading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-google-blue focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || loading}
            className="bg-google-blue text-white p-3 rounded-full hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200 shadow-lg hover:shadow-xl"
          >
            {loading ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              <Send className="w-6 h-6" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
