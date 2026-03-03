"use client";

import Link from 'next/link';
import { useState } from 'react';
import { DocMetadata } from '@/lib/docs';

interface DocsSidebarProps {
  docs: DocMetadata[];
  currentSlug: string;
}

export default function DocsSidebar({ docs, currentSlug }: DocsSidebarProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Mobile Hamburger Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden fixed top-4 right-4 z-50 p-2 bg-zinc-800 rounded-lg border border-zinc-700 text-zinc-400 hover:text-zinc-100 transition-colors"
        aria-label="Toggle documentation menu"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {isOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <nav className={`
        w-64 flex-shrink-0 border-r border-zinc-800 sticky top-12 h-[calc(100vh-3rem)] overflow-y-auto p-6
        hidden md:block
        fixed md:static top-0 left-0 h-full bg-zinc-900 md:bg-transparent z-40
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-500 uppercase tracking-wider">Documentation</h3>
          <ul className="space-y-2">
            {docs.map((doc) => (
              <li key={doc.slug}>
                <Link
                  href={`/docs/${doc.slug}`}
                  onClick={() => setIsOpen(false)}
                  className={`block text-sm transition-colors duration-200 ${currentSlug === doc.slug
                    ? 'text-zinc-100 font-medium'
                    : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                >
                  {doc.title}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </nav>
    </>
  );
}
