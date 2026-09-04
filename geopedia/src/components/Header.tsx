/**
 * Renders GeoPedia's primary site header and animated top-level navigation.
 *
 * The header provides persistent access to GeoPedia's branding and primary
 * application sections. Navigation destinations are defined separately from
 * their presentation so additional sections can be added without duplicating
 * navigation-link markup or styling.
 *
 * The currently active navigation destination is indicated by stronger text
 * weight and a shared underline. The underline is repositioned beneath the
 * active link whenever the current route changes, allowing it to smoothly
 * slide left or right between navigation destinations.
 *
 * Active navigation destinations are intentionally non-interactive. Selecting
 * the tab for the route that is already active does not trigger redundant
 * navigation, and active tabs do not use the normal hover treatment. This
 * behavior applies automatically to future navigation items added to the
 * shared navigation configuration.
 *
 * The GeoPedia brand link follows the same rule as the Home navigation tab and
 * does not trigger navigation while the root route is already active.
 *
 * The underline position is synchronized directly with the rendered navigation
 * elements rather than stored in React state. This avoids unnecessary
 * follow-up renders while keeping the visual indicator aligned with the active
 * navigation link.
 *
 * Navigation colors use GeoPedia's global semantic style tokens so the header
 * remains consistent with the rest of the application.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLayoutEffect, useRef } from "react";

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
 * The order of this array determines both the visual order of the links and
 * the direction in which the active underline travels when navigation changes.
 *
 * Additional top-level destinations can be added here without requiring
 * destination-specific active-click handling.
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
 * Shared structural styling for primary navigation links.
 *
 * Active and inactive interaction styles are applied separately because active
 * destinations are intentionally non-interactive and therefore do not receive
 * the normal hover treatment.
 */
const NAVIGATION_LINK_CLASSES = [
  "relative",
  "rounded-lg",
  "px-3",
  "py-2",
  "text-sm",
  "transition-colors",
  "duration-200",
].join(" ");

/**
 * Determines whether a navigation destination represents the current route.
 *
 * Home matches only the root route. Other destinations remain active for their
 * nested routes so, for example, a page beneath `/global` continues to
 * highlight the Global navigation tab.
 *
 * @param pathname - Current application pathname.
 * @param href - Navigation destination being tested.
 * @returns Whether the navigation destination is currently active.
 */
function isNavigationItemActive(
  pathname: string,
  href: string,
): boolean {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

/**
 * Displays GeoPedia's persistent site header and animated primary navigation.
 *
 * The active navigation link is measured after layout and a shared underline
 * element is moved beneath it. Because the same underline is reused for every
 * destination, changing routes produces a horizontal sliding transition rather
 * than separate underline enter and exit animations.
 *
 * Selecting an already active destination is prevented before navigation
 * occurs, avoiding unnecessary route work and keeping active tabs visually
 * distinct from interactive destinations.
 *
 * @returns GeoPedia's primary site header.
 */
export default function Header() {
  const pathname = usePathname();

  const navigationRef = useRef<HTMLElement | null>(null);
  const underlineRef = useRef<HTMLDivElement | null>(null);

  /**
   * Repositions the shared underline beneath the currently active navigation
   * link whenever the pathname changes.
   */
  useLayoutEffect(() => {
    const navigationElement = navigationRef.current;
    const underlineElement = underlineRef.current;

    if (!navigationElement || !underlineElement) {
      return;
    }

    const activeLinkElement =
      navigationElement.querySelector<HTMLAnchorElement>(
        '[data-active="true"]',
      );

    if (!activeLinkElement) {
      underlineElement.style.opacity = "0";
      return;
    }

    const navigationBounds =
      navigationElement.getBoundingClientRect();

    const activeLinkBounds =
      activeLinkElement.getBoundingClientRect();

    const horizontalOffset =
      activeLinkBounds.left - navigationBounds.left;

    underlineElement.style.width = `${activeLinkBounds.width}px`;

    underlineElement.style.transform = `translateX(${horizontalOffset}px)`;

    underlineElement.style.opacity = "1";
  }, [pathname]);

  return (
    <header className="relative z-50 flex h-14 items-center border-b border-border bg-background-1/95 px-4 shadow-sm backdrop-blur-md">
      {/* GeoPedia brand / Home link */}
      <Link
        href="/"
        onClick={(event) => {
          if (pathname === "/") {
            event.preventDefault();
          }
        }}
        className={[
          "flex items-center gap-2",
          pathname === "/" ? "cursor-default" : "",
        ].join(" ")}
      >
        {/* GeoPedia logo */}
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-button text-sm font-bold text-button-text">
          G
        </div>

        {/* Website name */}
        <span className="text-lg font-bold text-text">GeoPedia</span>
      </Link>

      {/* Primary navigation */}
      <nav
        ref={navigationRef}
        className="relative ml-8 flex h-full items-center gap-1"
        aria-label="Primary navigation"
      >
        {navigationItems.map(({ label, href }) => {
          const isActive = isNavigationItemActive(pathname, href);

          return (
            <Link
              key={href}
              href={href}
              onClick={(event) => {
                if (isActive) {
                  event.preventDefault();
                }
              }}
              data-active={isActive ? "true" : undefined}
              aria-current={isActive ? "page" : undefined}
              className={[
                NAVIGATION_LINK_CLASSES,
                isActive
                  ? "cursor-default font-bold text-text"
                  : "font-medium text-text-secondary hover:bg-background-3 hover:text-text",
              ].join(" ")}
            >
              {label}
            </Link>
          );
        })}

        {/* Animated active-navigation underline */}
        <div
          ref={underlineRef}
          aria-hidden="true"
          className={[
            "pointer-events-none absolute bottom-1.5 left-0 h-0.5",
            "bg-text opacity-0",
            "transition-[transform,width,opacity]",
            "duration-300 ease-in-out",
          ].join(" ")}
        />
      </nav>
    </header>
  );
}
