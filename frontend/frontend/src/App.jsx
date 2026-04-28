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

export default function App() {
  useEffect(() => {
    api.get("/ping/")
      .then(response => console.log("Backend Connection Status:", response.data.message))
      .catch(error => console.error("Backend Connection Error:", error));
  }, []);

  return (
    <BrowserRouter>
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