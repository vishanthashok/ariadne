import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ARIADNE | GPS-Denied Visual Navigation",
  description:
    "GPS-denied visual-inertial navigation for autonomous drone systems",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="h-screen overflow-hidden bg-background text-text-primary antialiased">
        {children}
      </body>
    </html>
  );
}
