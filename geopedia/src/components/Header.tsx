/**
 * Renders GeoPedia's primary site header and navigation.
 *
 * The header provides persistent access to GeoPedia's branding and primary
 * application sections. Navigation destinations are defined separately from
 * their presentation so additional sections can be added without duplicating
 * navigation-link markup or styling.
 *
 * This component is intentionally kept focused on the site's top-level
 * navigation so it can be expanded as GeoPedia gains additional global
 * controls and destinations.
 */

import Link from "next/link";

/**
 * Describes one destination displayed in the primary site navigation.
 */
type NavigationItem = {
  /** User-facing text displayed by the navigation link. */
  label: string;

  /** Application route opened by the navigation link. */
  href: string;
};

/**
 * Destinations displayed in GeoPedia's primary navigation.
 *
 * The order of this array determines the order in which links appear in the
 * header.
 */
const navigationItems: NavigationItem[] = [
  {
    label: "Home",
    href: "/",
  },
  {
    label: "Search",
    href: "/search",
  },
  {
    label: "Global",
    href: "/global",
  },
];

/**
 * Shared appearance of links displayed in the primary navigation.
 *
 * Keeping navigation styling in one place ensures new destinations
 * automatically match the existing header.
 */
const NAVIGATION_LINK_CLASSES = [
  "rounded-lg",
  "px-3",
  "py-2",
  "text-sm",
  "font-medium",
  "text-gray-600",
  "transition",
  "hover:bg-gray-300",
  "hover:text-black",
].join(" ");

/**
 * Displays GeoPedia's persistent site header.
 *
 * The header currently contains the GeoPedia brand link and primary
 * navigation. Its structure leaves room for additional site-wide controls
 * to be added as the application grows.
 *
 * @returns GeoPedia's primary site header.
 */
export default function Header() {
  return (
    <header className="relative z-50 flex h-14 items-center border-b border-gray-300 bg-white/95 px-4 shadow-sm backdrop-blur-md">
      {/* GeoPedia brand / home link */}
      <Link href="/" className="flex items-center gap-2">
        {/* GeoPedia logo */}
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-900 text-sm font-bold text-white">
          G
        </div>

        {/* Website name */}
        <span className="text-lg font-bold text-gray-900">
          GeoPedia
        </span>
      </Link>

      {/* Primary navigation */}
      <nav
        className="ml-8 flex h-full items-center gap-1"
        aria-label="Primary navigation"
      >
        {navigationItems.map(({ label, href }) => (
          <Link
            key={href}
            href={href}
            className={NAVIGATION_LINK_CLASSES}
          >
            {label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
