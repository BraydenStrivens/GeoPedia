import Image from "next/image";
import Link from "next/link";

import { getCountry } from "@/countries";
import { getCountryQuizzes } from "@/quiz/quizzes";

type CountryPageProps = {
  params: Promise<{
    country: string;
  }>;
};

export default async function CountryPage({ params }: CountryPageProps) {
  const { country: countryId } = await params;

  const country = getCountry(countryId);
  const quizzes = getCountryQuizzes(countryId);

  console.log("Country OBJ: ", country);

  if (!country) {
    return <div>Country not found</div>;
  }

  return (
    <main className="flex min-h-screen justify-center px-6 py-12">
      <div className="flex w-full max-w-6xl flex-col items-center">
        {/* Country Header */}
        <div className="mb-10 flex flex-col items-center text-center">
          <h1 className="text-5xl font-bold tracking-tight">{country.name}</h1>
          <p className="mt-2 text-2xl font-medium text-gray-500">
            {country.officialName}
          </p>
        </div>
        {/* Country Information */}
        <div className="flex w-full max-w-5xl items-stretch justify-center gap-6">
          {/* Flag */}
          <div className="flex h-70 w-80 items-center justify-center p-8 shadow-sm">
            <Image
              src={country.flagUrl}
              alt={`${country.name} flag`}
              width={240}
              height={160}
              className="h-auto max-h-full w-auto max-w-full"
            />
          </div>
          {/* Country Shape */}
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
          {/* Country Information */}
          <div className="flex h-70 w-80 flex-col justify-center rounded-xl border-gray-300 bg-gray-900 p-8 shadow-sm">
            <h2 className="mb-5 text-xl font-semibold"> Information </h2>
            <div className="flex flex-col gap-3 text-sm">
              <div className="flex justify-between gap-4">
                <span className="font-medium text-gray-500">Continent</span>
                <span className="text-right"> {country.continent} </span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="font-medium text-gray-500"> Region </span>
                <span className="text-right"> {country.region} </span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="font-medium text-gray-500">Capital</span>
                <span className="text-right"> {country.capital} </span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="font-medium text-gray-500">Population</span>
                <span className="text-right">
                  {country.population.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="font-medium text-gray-500">Driving</span>
                <span className="text-right">
                  {country.drivingSide === "right" ? "Right" : "Left"}
                </span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="font-medium text-gray-500">Calling Code</span>
                <span className="text-right"> {country.callingCode} </span>
              </div>
            </div>
          </div>
        </div>
        {/* Quizzes */}
        <section className="mt-12 w-full max-w-5xl">
          <h2 className="mb-6 text-center text-3xl font-bold">Quizzes</h2>
          {quizzes.length === 0 ? (
            <p className="text-center text-lg text-gray-500">
              Quizzes coming soon
            </p>
          ) : (
            <div className="flex flex-col items-center gap-3">
              {quizzes.map((quiz) => (
                <Link
                  key={quiz.id}
                  href={`/${country.id}/${quiz.id}`}
                  className="w-full max-w-xl rounded-lg border px-6 py-4 text-center font-medium shadow-sm transition hover:bg-gray-50 hover:text-black"
                >
                  {quiz.name}
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
