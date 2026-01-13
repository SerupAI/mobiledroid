import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return 'Never';
  return new Date(dateString).toLocaleString();
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'running':
      return 'text-green-500';
    case 'starting':
    case 'stopping':
      return 'text-yellow-500';
    case 'stopped':
      return 'text-gray-500';
    case 'error':
      return 'text-red-500';
    default:
      return 'text-gray-500';
  }
}

export function getStatusBgColor(status: string): string {
  switch (status) {
    case 'running':
      return 'bg-green-500/10 border-green-500/20';
    case 'starting':
    case 'stopping':
      return 'bg-yellow-500/10 border-yellow-500/20';
    case 'stopped':
      return 'bg-gray-500/10 border-gray-500/20';
    case 'error':
      return 'bg-red-500/10 border-red-500/20';
    default:
      return 'bg-gray-500/10 border-gray-500/20';
  }
}
