import { Inter, Noto_Sans_KR } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { AppShell } from "@/components/AppShell";

/**
 * Inter에는 한글 글리프가 없어 한글이 시스템 폰트로 대체된다. 그러면 "930만"처럼
 * 숫자와 한글이 섞인 라벨에서 두 폰트가 한 단어 안에 공존해 글자 크기·굵기·기준선이
 * 어긋나 보인다. 한글 전용 폰트를 함께 싣고 스택으로 묶어 그 대체를 없앤다.
 *
 * 숫자·영문은 Inter(표에 좋은 tabular 숫자), 한글은 Noto Sans KR이 맡는다.
 */
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-latin",
  display: "swap",
});

const notoSansKR = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "700", "900"],
  variable: "--font-kr",
  display: "swap",
});

export const metadata = {
  title: "Quant Miner Web",
  description: "Stock Quant Analysis Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning className={`${inter.variable} ${notoSansKR.variable}`}>
      <body>
        <Providers>
          <AppShell>
            {children}
          </AppShell>
        </Providers>
      </body>
    </html>
  );
}
