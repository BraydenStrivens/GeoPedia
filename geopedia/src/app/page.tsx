import Map from "@/components/map/Map";
import { worldMap } from "@/maps/configs/worldMap";

export default function Home() {
  return (
    <main className="h-[calc(100vh-3.5rem)] w-screen">
      <Map mapConfig={worldMap} clickBehavior="navigate" />
    </main>
  );
}
