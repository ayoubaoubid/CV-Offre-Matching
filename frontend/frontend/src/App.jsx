import { useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import CVUploader from "./components/CVUploader";
import Navbar from "./components/Navbar";
import CompanyProfilePage from "./pages/CompanyProfilePage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import NotificationsPage from "./pages/NotificationsPage";
import ProfilePage from "./pages/ProfilePage";
import RecruiterApplicationsPage from "./pages/RecruiterApplicationsPage";
import RecruiterCandidatesPage from "./pages/RecruiterCandidatesPage";
import RecruiterDashboardPage from "./pages/RecruiterDashboardPage";
import RecruiterJobFormPage from "./pages/RecruiterJobFormPage";
import RecruiterJobsPage from "./pages/RecruiterJobsPage";
import RecruiterRegisterPage from "./pages/RecruiterRegisterPage";
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
          <Route path="/register-recruiter" element={<RecruiterRegisterPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/upload" element={<CVUploader />} />
          <Route path="/recruiter" element={<RecruiterDashboardPage />} />
          <Route path="/recruiter/jobs" element={<RecruiterJobsPage />} />
          <Route path="/recruiter/jobs/new" element={<RecruiterJobFormPage />} />
          <Route path="/recruiter/jobs/:jobId/edit" element={<RecruiterJobFormPage />} />
          <Route path="/recruiter/jobs/:jobId/candidates" element={<RecruiterCandidatesPage />} />
          <Route path="/recruiter/applications" element={<RecruiterApplicationsPage />} />
          <Route path="/recruiter/company" element={<CompanyProfilePage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
