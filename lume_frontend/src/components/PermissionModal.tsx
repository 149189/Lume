'use client';

import { useState } from 'react';
import { X, Shield, Mail, Calendar, CheckSquare, StickyNote } from 'lucide-react';

interface PermissionModalProps {
  requiredPermissions: string[];
  onGrant: (permissions: Record<string, boolean>) => void;
  onCancel: () => void;
}

const SERVICE_INFO = {
  email: {
    icon: Mail,
    name: 'Gmail',
    color: 'blue',
    description: 'Send, read, and manage your emails',
  },
  calendar: {
    icon: Calendar,
    name: 'Google Calendar',
    color: 'red',
    description: 'Create and manage calendar events',
  },
  tasks: {
    icon: CheckSquare,
    name: 'Google Tasks',
    color: 'yellow',
    description: 'Create and manage your tasks',
  },
  keep: {
    icon: StickyNote,
    name: 'Google Keep',
    color: 'green',
    description: 'Create and read notes',
  },
};

export default function PermissionModal({
  requiredPermissions,
  onGrant,
  onCancel,
}: PermissionModalProps) {
  const [selectedPermissions, setSelectedPermissions] = useState<Record<string, boolean>>(
    requiredPermissions.reduce((acc, perm) => ({ ...acc, [perm]: true }), {})
  );

  const handleToggle = (permission: string) => {
    setSelectedPermissions((prev) => ({
      ...prev,
      [permission]: !prev[permission],
    }));
  };

  const handleGrant = () => {
    onGrant(selectedPermissions);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-green-500 text-white p-6 rounded-t-2xl">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8" />
              <h2 className="text-2xl font-bold">Grant Permissions</h2>
            </div>
            <button
              onClick={onCancel}
              className="text-white hover:bg-white hover:bg-opacity-20 p-1 rounded-lg transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          <p className="text-blue-50 text-sm">
            LUME needs access to complete your request
          </p>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-600 mb-4">
            To help you with this task, please grant access to the following services:
          </p>

          <div className="space-y-3">
            {requiredPermissions.map((permission) => {
              const info = SERVICE_INFO[permission as keyof typeof SERVICE_INFO];
              if (!info) return null;

              const Icon = info.icon;
              const isSelected = selectedPermissions[permission];

              return (
                <div
                  key={permission}
                  className={`border-2 rounded-xl p-4 transition-all cursor-pointer ${
                    isSelected
                      ? `border-google-${info.color} bg-${info.color}-50`
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleToggle(permission)}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-lg bg-${info.color}-100`}>
                      <Icon className={`w-6 h-6 text-google-${info.color}`} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-gray-800">{info.name}</h3>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleToggle(permission)}
                          className="w-5 h-5 text-google-blue rounded focus:ring-2 focus:ring-google-blue"
                        />
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{info.description}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> You can revoke these permissions at any time from your Google
              Account settings.
            </p>
          </div>

          {/* Actions */}
          <div className="mt-6 flex space-x-3">
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-3 border-2 border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleGrant}
              disabled={!Object.values(selectedPermissions).some((v) => v)}
              className="flex-1 px-4 py-3 bg-google-blue text-white font-medium rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors shadow-lg hover:shadow-xl"
            >
              Grant Access
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
