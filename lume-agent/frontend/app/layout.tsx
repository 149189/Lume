import type { Metadata } from 'next';
import './globals.css';
import { Roboto } from 'next/font/google';

const roboto = Roboto({ subsets: ['latin'], weight: ['400', '500', '700'] });

export const metadata: Metadata = {
  title: 'Lume • AI Productivity Agent',
  description: 'Chat with your Google-connected AI assistant',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${roboto.className} bg-white text-gray-900 antialiased`}>{children}</body>
    </html>
  );
}
