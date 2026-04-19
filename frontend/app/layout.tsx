import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dashy - Personal Monitoring Dashboard',
  description: 'Your personal monitoring dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
