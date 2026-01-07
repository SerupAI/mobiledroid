'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Send, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface TaskInputProps {
  profileId: string;
}

export function TaskInput({ profileId }: TaskInputProps) {
  const [prompt, setPrompt] = useState('');
  const queryClient = useQueryClient();

  const createTaskMutation = useMutation({
    mutationFn: async () => {
      const task = await api.createTask(profileId, prompt);
      // Execute immediately
      return api.executeTask(task.id);
    },
    onSuccess: () => {
      setPrompt('');
      queryClient.invalidateQueries({ queryKey: ['tasks', profileId] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || createTaskMutation.isPending) return;
    createTaskMutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe what you want the AI to do..."
        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 pr-12 text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 resize-none"
        rows={3}
        disabled={createTaskMutation.isPending}
      />
      <button
        type="submit"
        disabled={!prompt.trim() || createTaskMutation.isPending}
        className="absolute bottom-3 right-3 rounded-md bg-primary-600 p-2 text-white hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {createTaskMutation.isPending ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <Send className="h-5 w-5" />
        )}
      </button>
      {createTaskMutation.error && (
        <p className="mt-2 text-sm text-red-400">
          {(createTaskMutation.error as Error).message}
        </p>
      )}
    </form>
  );
}
