import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";

import api from "../services/api";

export default function GeoMap() {

  const [cities, setCities] = useState([]);

  useEffect(() => {

    api.get("/jobs/map-stats/")
      .then(res => setCities(res.data));

  }, []);

  return (
    <MapContainer
      center={[31.79, -7.09]}
      zoom={5}
      style={{ height: "500px" }}
    >

      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {cities.map((city, index) => (

        <CircleMarker
          key={index}
          center={[31, -7]}
          radius={10}
        >

          <Popup>
            <strong>{city.city}</strong>
            <br />
            {city.percent}% des offres
          </Popup>

        </CircleMarker>

      ))}

    </MapContainer>
  );
}