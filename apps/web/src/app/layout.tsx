import type { Metadata } from 'next';
import './globals.css';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { HeaderTelemetryBar } from '@/components/layout/HeaderTelemetryBar';

export const metadata: Metadata = {
  title: 'VOLTRON | Strategic AI Options Decision System',
  description: 'Find the edge. Stress the thesis. Trade only what survives.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-on-surface select-none antialiased">
        <AppSidebar />
        <div className="pl-64">
          <HeaderTelemetryBar />
          <main className="relative pt-16 min-h-screen bg-background p-container-gap overflow-x-hidden">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
