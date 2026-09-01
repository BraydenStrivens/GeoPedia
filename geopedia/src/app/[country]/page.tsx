/**
 * Renders the overview page for an individual GeoPedia country.
 *
 * The page displays:
 *
 * - The country's common and official names.
 * - Its flag and geographic silhouette.
 * - General country information.
 * - Links to every quiz currently registered for the country.
 *
 * Country metadata and quiz definitions are retrieved independently using
 * the country ID provided by the dynamic route.
 */

import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getCountry } from "@/countries";
import { getCountryQuizListings } from "@/quiz/quizzes";

/**
 * Route parameters supplied by Next.js for a country page.
 */
type CountryPageProps = {
  /** Dynamic route values for the current page. */
  params: Promise<{
    /** GeoPedia country ID taken from the URL. */
    country: string;
  }>;
};

/**
 * Describes one row displayed in the country's information panel.
 */
type CountryInformationItem = {
  /** User-facing name of the country property. */
  label: string;

  /** Formatted value displayed for the property. */
  value: string;
};

/**
 * Displays a country's general information and available geography quizzes.
 *
 * Invalid country IDs are forwarded to GeoPedia's Next.js 404 handling.
 *
 * @param props - Country page route properties.
 * @param props.params - Dynamic route parameters containing the country ID.
 * @returns The selected country's overview page.
 */
export default async function CountryPage({
  params,
}: CountryPageProps) {
  const { country: countryId } = await params;

  const country = getCountry(countryId);

  if (!country) {
    notFound();
  }

  const quizListings = await getCountryQuizListings(
    countryId,
    country.name,
  );

  /**
   * General country information displayed in the information card.
   */
  const countryInformation: CountryInformationItem[] = [
    {
      label: "Continent",
      value: country.continent,
    },
    {
      label: "Region",
      value: country.region,
    },
    {
      label: "Capital",
      value: country.capital,
    },
    {
      label: "Population",
      value: country.population.toLocaleString(),
    },
    {
      label: "Driving",
      value: country.drivingSide === "right" ? "Right" : "Left",
    },
    {
      label: "Calling Code",
      value: country.callingCode,
    },
  ];

  return (
    <main className="flex min-h-screen justify-center px-6 py-12">
      <div className="flex w-full max-w-6xl flex-col items-center">
        {/* Country heading */}
        <div className="mb-10 flex flex-col items-center text-center">
          {/* Common country name */}
          <h1 className="text-5xl font-bold tracking-tight">
            {country.name}
          </h1>

          {/* Official country name */}
          <p className="mt-2 text-2xl font-medium text-gray-500">
            {country.officialName}
          </p>
        </div>

        {/* Country visual and general information */}
        <div className="flex w-full max-w-5xl items-stretch justify-center gap-6">
          {/* Country flag */}
          <div className="flex h-70 w-80 items-center justify-center p-8 shadow-sm">
            <Image
              src={country.flagUrl}
              alt={`${country.name} flag`}
              width={240}
              height={160}
              className="h-auto max-h-full w-auto max-w-full"
            />
          </div>

          {/* Country silhouette */}
          <div className="flex h-70 w-80 items-center justify-center p-8 shadow-sm">
            <div
              className="h-full w-full bg-gray-500"
              style={{
                maskImage: `url(${country.imageUrl})`,
                WebkitMaskImage: `url(${country.imageUrl})`,
                maskSize: "contain",
                WebkitMaskSize: "contain",
                maskPosition: "center",
                WebkitMaskPosition: "center",
                maskRepeat: "no-repeat",
                WebkitMaskRepeat: "no-repeat",
              }}
            />
          </div>

          {/* Country information card */}
          <div className="flex h-70 w-80 flex-col justify-center rounded-xl border border-gray-300 bg-gray-900 p-8 shadow-sm">
            <h2 className="mb-5 text-xl font-semibold">
              Information
            </h2>

            {/* Country information rows */}
            <div className="flex flex-col gap-3 text-sm">
              {countryInformation.map(({ label, value }) => (
                <div
                  key={label}
                  className="flex justify-between gap-4"
                >
                  {/* Property name */}
                  <span className="font-medium text-gray-500">
                    {label}
                  </span>

                  {/* Property value */}
                  <span className="text-right">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Available country quizzes */}
        <section className="mt-12 w-full max-w-5xl">
          <h2 className="mb-6 text-center text-3xl font-bold">
            Quizzes
          </h2>

          {quizListings.length === 0 ? (
            /* Empty quiz state */
            <p className="text-center text-lg text-gray-500">
              Quizzes coming soon
            </p>
          ) : (
            /* Quiz links */
            <div className="flex flex-col items-center gap-3">
              {quizListings.map((quizListing) => (
                <Link
                  key={quizListing.id}
                  href={`/${country.id}/${quizListing.id}`}
                  className="w-full max-w-xl rounded-lg border px-6 py-4 text-center font-medium shadow-sm transition hover:bg-gray-50 hover:text-black"
                >
                  {quizListing.name}
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
