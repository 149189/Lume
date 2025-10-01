'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import ChatInterface from '@/components/ChatInterface';
import LoginScreen from '@/components/LoginScreen';
import PermissionModal from '@/components/PermissionModal';
import { apiClient, User } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  const [requiredPermissions, setRequiredPermissions] = useState<string[]>([]);
  const [oauthState, setOauthState] = useState<string>('');

  const checkAuth = async () => {
    try {
      const response = await apiClient.getUserInfo();
      setLoading(false);
      if (response.authenticated && response.user) {
        setUser(response.user);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    try {
      const response = await apiClient.initiateOAuth();
      window.location.href = response.auth_url;
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  useEffect(() => {
    // Check if user is already authenticated
    checkAuth();

    // Handle OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const authSuccess = urlParams.get('auth_success');
    const error = urlParams.get('error');
    const servicePermsGranted = urlParams.get('service_perms_granted');
    const code = urlParams.get('code');
    const state = urlParams.get('state');

    if (error) {
      console.error('OAuth error:', error);
    }

    // If we're being redirected from Google or from our callback
    if ((code && state) || authSuccess === 'true') {
      console.log('OAuth callback detected, clearing URL and checking auth...');
      // Clear URL parameters
      window.history.replaceState({}, document.title, '/');
      // Give backend time to set session cookie
      setTimeout(() => {
        checkAuth();
      }, 1500);
    }

    if (servicePermsGranted === 'true') {
      console.log('Service permissions granted');
      setShowPermissionModal(false);
      // Clear URL parameters
      window.history.replaceState({}, document.title, '/');
      setTimeout(() => {
        checkAuth();
      }, 1500);
    }
  }, []);

  const handleLogout = async () => {
    try {
      await apiClient.logout();
      setUser(null);
      setCurrentConversationId(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handlePermissionRequest = (permissions: string[], state: string) => {
    setRequiredPermissions(permissions);
    setOauthState(state);
    setShowPermissionModal(true);
  };

  const handlePermissionGrant = async (permissions: Record<string, boolean>) => {
    try {
      const response = await apiClient.requestServicePermissions(oauthState, permissions);
      window.location.href = response.auth_url;
    } catch (error) {
      console.error('Permission request failed:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-google-blue"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar
        user={user}
        currentConversationId={currentConversationId}
        onConversationSelect={setCurrentConversationId}
        onLogout={handleLogout}
      />
      <ChatInterface
        user={user}
        conversationId={currentConversationId}
        onConversationCreate={setCurrentConversationId}
        onPermissionRequest={handlePermissionRequest}
      />
      {showPermissionModal && (
        <PermissionModal
          requiredPermissions={requiredPermissions}
          onGrant={handlePermissionGrant}
          onCancel={() => setShowPermissionModal(false)}
        />
      )}
    </div>
  );
}
