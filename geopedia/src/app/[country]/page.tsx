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
import { notFound } from "next/navigation";

import QuizListingRow from "@/components/quiz/QuizListingRow";
import QuizPageHero from "@/components/quiz/QuizPageHero";
import QuizSectionHeader from "@/components/quiz/QuizSectionHeader";
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
      value: `+${country.callingCode}`,
    },
  ];

  return (
    <main className="min-h-screen bg-slate-300">
      {/* Country heading */}
      <QuizPageHero
        title={country.name}
        subtitle={country.officialName}
      />

      <div className="mx-auto flex w-full max-w-6xl flex-col items-center px-6 py-10">
        {/* Country visual and general information */}
        <div className="grid w-full max-w-5xl gap-6 md:grid-cols-3">
          {/* Country flag */}
          <div
            className="  
              flex h-70 items-center justify-center
              rounded-xl border border-slate-400
              bg-white p-8 shadow-md
            "
          >
            <Image
              src={country.flagUrl}
              alt={`${country.name} flag`}
              width={240}
              height={160}
              className="h-auto max-h-full w-auto max-w-full border border-gray-300"
            />
          </div>

          {/* Country silhouette */}
          <div
            className="
              flex h-70 items-center justify-center
              rounded-xl border border-slate-400
              bg-slate-100 p-8 shadow-md
            "
          >
            <div
              className="h-full w-full bg-slate-500"
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
          <div
            className="
              flex h-70 flex-col justify-center 
              rounded-xl border border-slate-400
              bg-slate-100 p-8 shadow-md
            "
          >
            <h2 className="mb-5 text-xl font-semibold text-slate-900">
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
                  <span className="font-medium text-slate-500">
                    {label}
                  </span>

                  {/* Property value */}
                  <span className="text-right font-semibold text-slate-900">
                    {value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Available country quizzes */}
        <section className="mt-12 w-full max-w-5xl">
          <QuizSectionHeader
            description={`Choose a quiz to start practicing ${country.name}.`}
          />

          {quizListings.length === 0 ? (
            /* Empty quiz state */
            <p className="text-center text-lg text-slate-500">
              Quizzes coming soon
            </p>
          ) : (
            /* Quiz listings */
            <div className="mx-auto flex w-full max-w-2xl flex-col gap-3">
              {quizListings.map((quizListing) => (
                <QuizListingRow
                  key={quizListing.id}
                  quizListing={quizListing}
                  href={`/${country.id}/${quizListing.id}`}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
