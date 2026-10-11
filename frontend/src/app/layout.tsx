import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "دستیار هوشمند DevOps",
  description: "دستیار داخلی عیب‌یابی زیرساخت بر پایه‌ی مستندات تأییدشده‌ی تیم",
  icons: { icon: "/favicon.svg" },
};

// Runs before first paint so the saved theme / direction never flashes.
const initPreferences = `(function(){try{var r=document.documentElement,t=localStorage.getItem('theme'),d=t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches;if(d)r.classList.add('dark');r.style.colorScheme=d?'dark':'light';var x=localStorage.getItem('dir');if(x==='ltr'||x==='rtl')r.dir=x;}catch(e){}})();`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fa" dir="rtl" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: initPreferences }} />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
