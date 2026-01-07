'use client';

import { useMutation } from '@tanstack/react-query';
import { Home, ArrowLeft, RotateCcw, Keyboard } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface DeviceControlsProps {
  profileId: string;
}

export function DeviceControls({ profileId }: DeviceControlsProps) {
  const backMutation = useMutation({
    mutationFn: () => api.pressBack(profileId),
  });

  const homeMutation = useMutation({
    mutationFn: () => api.pressHome(profileId),
  });

  const buttonClass = cn(
    'flex items-center justify-center rounded-lg bg-gray-800 p-3',
    'hover:bg-gray-700 transition-colors disabled:opacity-50'
  );

  return (
    <div className="flex items-center justify-center gap-4">
      <button
        onClick={() => backMutation.mutate()}
        disabled={backMutation.isPending}
        className={buttonClass}
        title="Back"
      >
        <ArrowLeft className="h-5 w-5" />
      </button>

      <button
        onClick={() => homeMutation.mutate()}
        disabled={homeMutation.isPending}
        className={buttonClass}
        title="Home"
      >
        <Home className="h-5 w-5" />
      </button>

      <button className={buttonClass} title="Recent Apps">
        <RotateCcw className="h-5 w-5" />
      </button>
    </div>
  );
}
