import { MapContainer, TileLayer, Marker } from "react-leaflet";

export default function GeoMap() {
  return (
    <MapContainer center={[31.63, -8]} zoom={6} style={{ height: "400px" }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Marker position={[33.57, -7.58]} />
    </MapContainer>
  );
}