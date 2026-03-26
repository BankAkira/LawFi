import type { Metadata } from "next";
import { Noto_Sans_Thai } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import GoogleAuthWrapper from "@/components/GoogleAuthWrapper";
import Navbar from "@/components/Navbar";

const notoSansThai = Noto_Sans_Thai({
  variable: "--font-noto-thai",
  subsets: ["thai", "latin"],
});

export const metadata: Metadata = {
  title: "LawFi - ค้นหากฎหมายและฎีกาไทย",
  description:
    "แพลตฟอร์มค้นหาและวิเคราะห์กฎหมายไทยและคำพิพากษาศาลฎีกา ด้วย AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th" className={`${notoSansThai.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-[family-name:var(--font-noto-thai)] bg-gray-50 text-gray-900">
        <GoogleAuthWrapper>
          <AuthProvider>
            <Navbar />
            <main className="flex-1">{children}</main>
          </AuthProvider>
        </GoogleAuthWrapper>
      </body>
    </html>
  );
}
