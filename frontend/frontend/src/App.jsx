import { useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ProfilePage from "./pages/ProfilePage";
import DashboardPage from "./pages/DashboardPage";
import ResultsPage from "./pages/ResultsPage";
import Navbar from "./components/Navbar";
import CVUploader from "./components/CVUploader";
import api from "./services/api";

export default function App() { // composant principal de l’application qui gère les routes et la navigation
  useEffect(() => { // test de communicationentrele Frontend et le Backend
    api.get("/ping/") // envoie une requête GET à l’endpoint /ping/ du backend pour vérifier la connexion
      .then(response => console.log("Backend Connection Status:", response.data.message))
      .catch(error => console.error("Backend Connection Error:", error));
  }, []);

  return (
    <BrowserRouter> {/** gère la navigation entre les différentes pages */}
      <Navbar />
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/upload" element={<CVUploader />} />
      </Routes>
    </BrowserRouter>
  );
}