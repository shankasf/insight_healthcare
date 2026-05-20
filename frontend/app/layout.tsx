import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Insight Healthcare Clinic — Assistant",
  description:
    "Chat with the Insight Healthcare Clinic assistant about appointments, insurance, and clinic information.",
  icons: { icon: "/favicon.ico" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f9fafb",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-full bg-gray-50 text-gray-900">{children}</body>
    </html>
  );
}
