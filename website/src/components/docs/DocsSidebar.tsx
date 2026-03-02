import Link from 'next/link';
import { DocMetadata } from '@/lib/docs';

interface DocsSidebarProps {
  docs: DocMetadata[];
  currentSlug: string;
}

export default function DocsSidebar({ docs, currentSlug }: DocsSidebarProps) {
  return (
    <nav className="w-64 flex-shrink-0 border-r border-zinc-800 sticky top-[5.25rem] h-[calc(100vh-5.25rem)] overflow-y-auto p-6 hidden md:block">
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-zinc-500 uppercase tracking-wider">Documentation</h3>
        <ul className="space-y-2">
          {docs.map((doc) => (
            <li key={doc.slug}>
              <Link
                href={`/docs/${doc.slug}`}
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
  );
}
