import type { Metadata } from 'next';
import './globals.css';
import { Sidebar } from '@/components/Sidebar';
import { AppProvider } from '@/lib/store';

export const metadata: Metadata = {
  title: 'AI Research Studio — From Synthetic Users to Product Decisions',
  description: 'AI-driven UX research platform transforming synthetic customer cohorts into evidence-backed product decisions.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full bg-slate-50 text-slate-900 flex overflow-hidden">
        <AppProvider>
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0 h-full overflow-y-auto">
            {children}
          </div>
        </AppProvider>
      </body>
    </html>
  );
}
