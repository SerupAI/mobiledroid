'use client';

import Link from 'next/link';
import { Plus } from 'lucide-react';

export function CreateProfileCard() {
  return (
    <Link
      href="/profiles/new"
      className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-700 p-8 text-gray-400 hover:border-primary-500 hover:text-primary-500 transition-colors min-h-[200px]"
    >
      <Plus className="h-10 w-10 mb-2" />
      <span className="font-medium">Create New Profile</span>
    </Link>
  );
}
