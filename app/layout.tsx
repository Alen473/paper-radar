import type { Metadata } from 'next';
import { Noto_Sans_SC, Noto_Serif_SC } from 'next/font/google';
import './globals.css';

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
const siteOrigin = process.env.NEXT_PUBLIC_SITE_ORIGIN || 'http://localhost:4173';

const sans = Noto_Sans_SC({
  variable: '--font-sans',
  subsets: ['latin'],
  display: 'swap',
});

const serif = Noto_Serif_SC({
  variable: '--font-serif',
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL(siteOrigin),
  title: '文献雷达｜再生生物学与软骨研究',
  description: '面向再生生物学、软骨发育与基因调控研究者的文献发现与阅读网站。',
  openGraph: {
    title: '文献雷达｜再生生物学与软骨研究',
    description: '发现值得读的再生生物学、软骨发育与基因调控文献。',
    images: [`${basePath}/paper-radar-social.png`],
    type: 'website',
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body className={`${sans.variable} ${serif.variable}`}>{children}</body>
    </html>
  );
}
