/**
 * Downloads GeoPedia's raw REST Countries v5 country metadata.
 *
 * REST Countries is used as a build-time metadata source for information such
 * as country languages and native country names. The downloaded data is kept
 * under data/raw and is consumed by later processing/generation scripts; the
 * GeoPedia website does not call REST Countries at runtime.
 *
 * The REST Countries free plan limits responses to 100 records, so this script
 * follows the API's offset pagination until every reported record has been
 * downloaded.
 *
 * The API key must be provided through the REST_COUNTRIES_API_KEY environment
 * variable and is never written to the output file.
 *
 * Run from the repository root with:
 *
 *   npx tsx scripts/global/countries/download/download-rest-countries.ts
 */

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const API_URL = "https://api.restcountries.com/countries/v5";
const PAGE_LIMIT = 100;

const OUTPUT_PATH = path.resolve(
  "data/raw/global/countries/rest-countries-v5.json",
);

const REST_COUNTRY_CODE_ALIASES: Readonly<Record<string, string>> = {
  UNK: "XKX",
};

interface RestCountriesResponse {
  data?: {
    objects?: unknown[];
    meta?: {
      total?: number;
      count?: number;
      limit?: number;
      offset?: number;
      more?: boolean;
    };
  };
  success?: boolean;
  errors?: Array<{
    message?: string;
  }>;
}

interface CountryWithCode {
  codes?: {
    alpha_3?: string;
  };
}

/**
 * Downloads one REST Countries page.
 *
 * @param apiKey - REST Countries bearer token.
 * @param offset - Number of records to skip before this page.
 * @returns Parsed REST Countries response.
 */
async function downloadPage(
  apiKey: string,
  offset: number,
): Promise<RestCountriesResponse> {
  const url = new URL(API_URL);
  url.searchParams.set("limit", String(PAGE_LIMIT));
  url.searchParams.set("offset", String(offset));

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${apiKey}`,
    },
  });

  if (!response.ok) {
    throw new Error(
      `REST Countries request failed with HTTP ${response.status} ${response.statusText}.`,
    );
  }

  const data = (await response.json()) as RestCountriesResponse;

  if (data.success === false) {
    const messages =
      data.errors
        ?.map((error) => error.message)
        .filter((message): message is string => Boolean(message))
        .join("; ") ?? "Unknown REST Countries API error.";

    throw new Error(messages);
  }

  return data;
}

/**
 * Returns the ISO-3 country code when one is present on a REST Countries
 * object.
 */
function getAlpha3Code(country: unknown): string | undefined {
  if (!country || typeof country !== "object") {
    return undefined;
  }

  const candidate = country as CountryWithCode;
  const rawCode = candidate.codes?.alpha_3;

  if (typeof rawCode !== "string" || rawCode.length === 0) {
    return undefined;
  }

  return REST_COUNTRY_CODE_ALIASES[rawCode] ?? rawCode;
}

/**
 * Downloads every REST Countries record using offset pagination.
 */
async function downloadAllCountries(
  apiKey: string,
): Promise<unknown[]> {
  const countries: unknown[] = [];

  let offset = 0;
  let expectedTotal: number | undefined;

  while (true) {
    console.log(
      `Downloading REST Countries records ${offset + 1}-${offset + PAGE_LIMIT}...`,
    );

    const response = await downloadPage(apiKey, offset);
    const objects = response.data?.objects;
    const meta = response.data?.meta;

    if (!Array.isArray(objects)) {
      throw new Error(
        `REST Countries response at offset ${offset} did not contain data.objects.`,
      );
    }

    if (!meta || typeof meta.total !== "number") {
      throw new Error(
        `REST Countries response at offset ${offset} did not contain valid pagination metadata.`,
      );
    }

    if (expectedTotal === undefined) {
      expectedTotal = meta.total;
    } else if (meta.total !== expectedTotal) {
      throw new Error(
        `REST Countries total changed during download: expected ${expectedTotal}, received ${meta.total}.`,
      );
    }

    countries.push(...objects);

    if (!meta.more) {
      break;
    }

    if (objects.length === 0) {
      throw new Error(
        `REST Countries reported more records at offset ${offset} but returned an empty page.`,
      );
    }

    offset += objects.length;
  }

  if (
    expectedTotal !== undefined &&
    countries.length !== expectedTotal
  ) {
    throw new Error(
      `Downloaded ${countries.length} REST Countries records, but the API reported ${expectedTotal}.`,
    );
  }

  return countries;
}

/**
 * Reports ISO-3 coverage problems without assuming REST Countries has exactly
 * one record for every GeoPedia map feature.
 */
function reportCodeCoverage(countries: unknown[]): void {
  const counts = new Map<string, number>();
  let missingCodeCount = 0;

  for (const country of countries) {
    const code = getAlpha3Code(country);

    if (!code) {
      missingCodeCount += 1;
      continue;
    }

    counts.set(code, (counts.get(code) ?? 0) + 1);
  }

  const duplicateCodes = [...counts.entries()]
    .filter(([, count]) => count > 1)
    .sort(([first], [second]) => first.localeCompare(second));

  console.log(`Downloaded records: ${countries.length}`);
  console.log(`Unique ISO-3 codes: ${counts.size}`);

  if (missingCodeCount > 0) {
    console.warn(
      `Records without an ISO-3 code: ${missingCodeCount}`,
    );
  }

  if (duplicateCodes.length > 0) {
    console.warn("Duplicate ISO-3 codes:");

    for (const [code, count] of duplicateCodes) {
      console.warn(`  ${code}: ${count} records`);
    }
  }
}

/**
 * Downloads and saves the raw REST Countries dataset.
 */
async function main(): Promise<void> {
  const apiKey = process.env.REST_COUNTRIES_API_KEY;

  if (!apiKey) {
    throw new Error(
      "REST_COUNTRIES_API_KEY is not set. Set it in the current shell before running this script.",
    );
  }

  const countries = await downloadAllCountries(apiKey);

  reportCodeCoverage(countries);

  await mkdir(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  await writeFile(
    OUTPUT_PATH,
    `${JSON.stringify(countries, null, 2)}\n`,
    "utf8",
  );

  console.log(`Saved REST Countries data to ${OUTPUT_PATH}`);
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);

  process.exitCode = 1;
});
