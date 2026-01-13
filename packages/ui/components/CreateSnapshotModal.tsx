'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Camera, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface CreateSnapshotModalProps {
  profileId: string;
  profileName: string;
  onClose: () => void;
}

export function CreateSnapshotModal({ profileId, profileName, onClose }: CreateSnapshotModalProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(`${profileName} - ${new Date().toLocaleDateString()}`);
  const [description, setDescription] = useState('');

  const createMutation = useMutation({
    mutationFn: () => api.createSnapshot(profileId, name, description || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
      onClose();
    },
    onError: (error: Error) => {
      alert(`Failed to create snapshot: ${error.message}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createMutation.mutate();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-800 rounded-lg w-full max-w-md mx-4 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Camera className="h-5 w-5 text-primary-500" />
            <h2 className="text-lg font-semibold">Create Snapshot</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-white rounded"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Snapshot Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter snapshot name"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Description (optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What state is this snapshot capturing?"
              rows={3}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>

          <div className="text-sm text-gray-400 bg-gray-800/50 p-3 rounded">
            <p>This will create a snapshot of the device's current state including:</p>
            <ul className="list-disc list-inside mt-1 space-y-0.5">
              <li>Installed apps and their data</li>
              <li>System settings</li>
              <li>User files</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-300 bg-gray-800 rounded-lg hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim() || createMutation.isPending}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Camera className="h-4 w-4" />
                  Create Snapshot
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
