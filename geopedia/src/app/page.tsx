import Map from "@/components/Map";
// import { usStatesMap } from "@/maps/usStates";
import { worldMap } from "@/maps/worldMap";
// import { usStatesQuiz } from "@/quizzes/usStates";

export default function Home() {
  return (
    <main className="h-[calc(100vh-3.5rem)] w-screen">
      <Map mapConfig={worldMap} clickBehavior="navigate" />
    </main>
  );
}
