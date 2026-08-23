/**
 * Defines GeoPedia's root application layout.
 *
 * The root layout configures the site's fonts and metadata and provides the
 * shared page structure used by every route. GeoPedia's persistent header is
 * rendered above each route's page content.
 */

import "./globals.css";

import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import Header from "@/components/Header";

/**
 * Primary sans-serif font used throughout GeoPedia.
 */
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

/**
 * Monospace font available throughout GeoPedia.
 */
const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

/**
 * Default metadata applied to GeoPedia pages.
 */
export const metadata: Metadata = {
  title: "GeoPedia",
  description:
    "Interactive geography quizzes for learning countries, regions, and more.",
};

/**
 * Provides the shared document structure used by every GeoPedia route.
 *
 * @param props - Root layout properties supplied by Next.js.
 * @param props.children - Page content belonging to the active route.
 * @returns GeoPedia's root HTML document and shared application layout.
 */
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col">
        {/* Persistent site header */}
        <Header />

        {/* Active route content */}
        {children}
      </body>
    </html>
  );
}
