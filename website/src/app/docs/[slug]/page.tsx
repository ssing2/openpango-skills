import { getDocBySlug, getAllDocs, getDocSlugs } from '@/lib/docs';
import { MDXRemote } from 'next-mdx-remote/rsc';
import DocsSidebar from '@/components/docs/DocsSidebar';
import MDXComponents from '@/components/docs/MDXComponents';
import { notFound } from 'next/navigation';

export async function generateStaticParams() {
  const slugs = getDocSlugs();
  return slugs.map((slug) => ({
    slug: slug.replace(/\.mdx$/, ''),
  }));
}

export default async function DocPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let doc;
  try {
    doc = getDocBySlug(slug);
  } catch {
    notFound();
  }

  const { metadata, content } = doc;
  const docs = getAllDocs();

  return (
    <div className="flex min-h-screen bg-[#0a0a0a] text-zinc-300 pt-[5.25rem]">
      <DocsSidebar docs={docs} currentSlug={slug} />
      <main className="flex-1 max-w-4xl mx-auto px-6 py-12">
        <header className="mb-12">
          <h1 className="text-zinc-500 font-mono text-sm uppercase tracking-[0.2em] mb-4">
            / Documentation / {metadata.slug}
          </h1>
          <p className="text-zinc-400 text-lg font-light max-w-2xl leading-relaxed">
            {metadata.description}
          </p>
        </header>
        <div className="prose prose-zinc prose-invert max-w-none">
          <MDXRemote source={content} components={MDXComponents} />
        </div>
      </main>
    </div>
  );
}
