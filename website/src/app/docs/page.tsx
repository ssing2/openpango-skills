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
    <main className="min-h-screen bg-[#0a0a0a] pt-32 pb-32 px-6">
      <div className="max-w-5xl mx-auto relative z-10">
        <div>
          <div className="text-[10px] tracking-[0.3em] text-[#ff3e00] border border-[#ff3e00]/30 bg-[#ff3e00]/5 px-4 py-1.5 inline-block mb-6 uppercase font-bold">
            DOCUMENTATION
          </div>
          <h1 className="text-5xl md:text-7xl font-black uppercase tracking-tighter mb-8 leading-none">
            System <br /><span className="text-zinc-500">Architecture</span>
          </h1>
          <p className="text-sm text-zinc-500 max-w-2xl mb-16 leading-relaxed">
            OpenPango is governed by rigid rules and transparent workflows. Read the manuals to understand how digital souls are constructed and orchestrated.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {docs.map((doc) => (
            <Link
              key={doc.slug}
              href={`/docs/${doc.slug}`}
              className="group brutal-card p-8 block"
            >
              <div className="bg-white/5 w-12 h-12 flex items-center justify-center text-[#ff3e00] group-hover:bg-[#ff3e00] group-hover:text-white transition-colors mb-6">
                {iconMap[doc.title] || <BookOpen />}
              </div>
              <h3 className="text-lg font-bold uppercase tracking-tight mb-3">{doc.title}</h3>
              <p className="text-sm text-zinc-500">{doc.description}</p>

              <div className="mt-8 text-[10px] tracking-[0.2em] text-[#ff3e00] uppercase opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                READ CHAPTER →
              </div>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
