/**
 * Renders GeoPedia's home page.
 *
 * The home page displays the interactive world map, which acts as the
 * application's primary country-navigation interface. Selecting a supported
 * country navigates the user to that country's page.
 */

import BaseWorldNavigationMap from "@/components/map/BaseWorldNavigationMap";
import { worldMap } from "@/maps/configs/worldMap";
import { getCountryIdsWithQuizzes } from "@/quiz/quizzes";

/**
 * Displays GeoPedia's interactive world map.
 *
 * The map uses `navigate` click behavior so selecting a geographic feature
 * can navigate to the corresponding country page.
 *
 * @returns GeoPedia's home page.
 */
export default async function Home() {
  const countryIdsWithQuizzes = await getCountryIdsWithQuizzes();

  return (
    <main className="h-[calc(100vh-3.5rem)] w-screen">
      {/* Interactive world navigation map */}
      <BaseWorldNavigationMap
        mapConfig={worldMap}
        countryIdsWithQuizzes={countryIdsWithQuizzes}
      />
    </main>
  );
}
