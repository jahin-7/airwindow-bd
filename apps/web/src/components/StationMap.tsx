"use client";

import "leaflet/dist/leaflet.css";
import { CircleMarker, MapContainer, TileLayer, Tooltip } from "react-leaflet";
import type { Station } from "@/lib/api";

/** Pins only at monitoring stations; nothing is drawn between them. */
export default function StationMap({ stations, selected, onPick, lang }: {
  stations: Station[]; selected: string; onPick: (id: string) => void; lang: "en" | "bn" | null;
}) {
  return (
    <MapContainer center={[23.7, 90.35]} zoom={6.4} scrollWheelZoom={false}
      className="h-72 w-full overflow-hidden rounded-[var(--radius-card)]" attributionControl>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />
      {stations.map((s) => (
        <CircleMarker key={s.id} center={[s.lat, s.lon]} radius={s.id === selected ? 10 : 7}
          pathOptions={{ color: "#3b7bff", fillColor: s.id === selected ? "#3b7bff" : "#ffffff", fillOpacity: 1, weight: 3 }}
          eventHandlers={{ click: () => onPick(s.id) }}>
          <Tooltip>{lang === "bn" ? s.name_bn : s.name}</Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
