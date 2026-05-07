import { useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import CVUploader from "./components/CVUploader";
import Navbar from "./components/Navbar";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";
import RegisterPage from "./pages/RegisterPage";
import ResultsPage from "./pages/ResultsPage";
import api from "./services/api";


export default function App() {
  useEffect(() => {
    api
      .get("/ping/")
      .then((response) => console.log("Backend Connection Status:", response.data.message))
      .catch((error) => console.error("Backend Connection Error:", error));
  }, []);

  return (
    <BrowserRouter>
      <div className="site-shell">
        <Navbar />
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/upload" element={<CVUploader />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
