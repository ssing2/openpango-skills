import { BookOpen, Terminal, Shield, Zap } from "lucide-react";
import Link from 'next/link';
import { getAllDocs } from '@/lib/docs';

export default async function DocsPage() {
  const docs = getAllDocs();

  const iconMap: Record<string, React.ReactNode> = {
    'Workspace Contract': <Terminal />,
    'Agent Lifecycle': <Zap />,
    'CLI Reference': <Terminal />,
    'Bounty Program': <Shield />,
    'Memory & State': <BookOpen />,
    'Security Models': <Shield />,
  };

  return (
    <main className="min-h-screen bg-[#09090b] pt-28 pb-32 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-14">
          <p className="text-[13px] font-medium text-[#ff4d00] mb-4">Documentation</p>
          <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-white mb-4 leading-snug">
            System Architecture
          </h1>
          <p className="text-[15px] text-zinc-400 max-w-2xl leading-relaxed">
            OpenPango is governed by rigid rules and transparent workflows. Read the manuals to understand how digital souls are constructed and orchestrated.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-3">
          {docs.map((doc) => (
            <Link
              key={doc.slug}
              href={`/docs/${doc.slug}`}
              className="card p-7 block group"
            >
              <div className="w-10 h-10 flex items-center justify-center rounded-lg bg-white/[0.04] text-zinc-400 group-hover:text-[#ff4d00] transition-colors mb-5">
                {iconMap[doc.title] || <BookOpen className="w-5 h-5" />}
              </div>
              <h3 className="text-[16px] font-medium text-zinc-200 mb-2">{doc.title}</h3>
              <p className="text-[13px] text-zinc-500 leading-relaxed">{doc.description}</p>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
