import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Remand",
  description: "Find and validate demand from Reddit conversations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
