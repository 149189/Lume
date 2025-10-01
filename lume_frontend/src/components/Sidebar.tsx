'use client';

import { useState, useEffect } from 'react';
import { MessageSquare, Plus, LogOut, User as UserIcon, Sparkles } from 'lucide-react';
import { apiClient, User, Conversation } from '@/lib/api';

interface SidebarProps {
  user: User;
  currentConversationId: number | null;
  onConversationSelect: (id: number | null) => void;
  onLogout: () => void;
}

export default function Sidebar({
  user,
  currentConversationId,
  onConversationSelect,
  onLogout,
}: SidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const data = await apiClient.getConversations();
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    onConversationSelect(null);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-screen">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-6 h-6 text-google-blue" />
            <h1 className="text-2xl font-bold">
              <span className="text-google-blue">L</span>
              <span className="text-google-red">U</span>
              <span className="text-google-yellow">M</span>
              <span className="text-google-green">E</span>
            </h1>
          </div>
        </div>

        <button
          onClick={handleNewChat}
          className="w-full bg-google-blue text-white font-medium py-2.5 px-4 rounded-lg hover:bg-blue-600 transition-colors duration-200 flex items-center justify-center space-x-2 shadow-sm"
        >
          <Plus className="w-5 h-5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="text-center text-gray-500 py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-google-blue"></div>
          </div>
        ) : conversations.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No conversations yet</p>
            <p className="text-xs mt-1">Start a new chat to begin</p>
          </div>
        ) : (
          <div className="space-y-2">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => onConversationSelect(conversation.id)}
                className={`w-full text-left p-3 rounded-lg transition-all duration-200 ${
                  currentConversationId === conversation.id
                    ? 'bg-blue-50 border-2 border-google-blue'
                    : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                }`}
              >
                <div className="flex items-start space-x-2">
                  <MessageSquare className="w-4 h-4 mt-1 text-gray-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm text-gray-800 truncate">
                      {conversation.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDate(conversation.updated_at)} · {conversation.message_count} messages
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* User Profile */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-3">
          {user.profile_picture ? (
            <img
              src={user.profile_picture}
              alt={user.username}
              className="w-10 h-10 rounded-full border-2 border-gray-200"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-google-blue flex items-center justify-center">
              <UserIcon className="w-6 h-6 text-white" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">{user.username}</p>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
          </div>
          <button
            onClick={onLogout}
            className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors duration-200"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>

        {/* Permission Status */}
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-600 mb-2">Active Permissions:</p>
          <div className="flex flex-wrap gap-1">
            {user.permissions.email && (
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">Gmail</span>
            )}
            {user.permissions.calendar && (
              <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">Calendar</span>
            )}
            {user.permissions.tasks && (
              <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">Tasks</span>
            )}
            {user.permissions.keep && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">Keep</span>
            )}
            {!Object.values(user.permissions).some((v) => v) && (
              <span className="text-xs text-gray-500">None granted yet</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
