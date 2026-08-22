/**
 * Renders GeoPedia's primary site header and navigation.
 *
 * The header displays the GeoPedia logo and provides links to the main
 * sections of the application. Next.js Link components are used for
 * client-side navigation between routes.
 */

import Link from "next/link";

/**
 * Displays the persistent GeoPedia site header and navigation links.
 */
export default function Header() {
  return (
    <header className="realtive z-50 flex h-14 items-center border-b border-gray-200 bg-white/95 px-4 shadow-sm backdrop-blur-md">
      {/* Logo / website name */}
      <Link href="/" className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-900 text-sm font-bold text-white">
          G
        </div>

        <span className="text-lg font-bold text-gray-900">GeoPedia</span>
      </Link>

      {/* Navigation */}
      <nav className="ml-8 flex h-full items-center gap-1">
        <Link
          href="/"
          className="rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition hover:bg-gray-100 hover:text-gray-900"
        >
          Home
        </Link>

        <Link
          href="/search"
          className="rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition hover:bg-gray-100 hover:text-gray-900"
        >
          Search
        </Link>

        <Link
          href="/global"
          className="rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition hover:bg-gray-100 hover:text-gray-900"
        >
          Global
        </Link>
      </nav>
    </header>
  );
}
