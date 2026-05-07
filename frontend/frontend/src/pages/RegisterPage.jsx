import { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import { registerUser } from "../services/authService";


const initialForm = {
  first_name: "",
  last_name: "",
  email: "",
  password: "",
  confirm_password: "",
  title: "",
  location: "",
  experience_years: 0,
  education_level: "",
  phone: "",
  linkedin_url: "",
  bio: "",
};


export default function RegisterPage() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const payload = {
        ...form,
        experience_years: Number(form.experience_years || 0),
      };
      const response = await registerUser(payload);
      login({
        user: response.data.user,
        tokens: response.data.tokens,
      });
      setMessage("Compte cree avec succes. Vous pouvez maintenant ajouter votre CV.");
      setTimeout(() => navigate("/upload"), 800);
    } catch (requestError) {
      const serverData = requestError.response?.data;
      if (typeof serverData === "string") {
        setError(serverData);
      } else if (serverData?.confirm_password?.[0]) {
        setError(serverData.confirm_password[0]);
      } else if (serverData?.email?.[0]) {
        setError(serverData.email[0]);
      } else {
        setError("Creation du compte impossible.");
      }
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  return (
    <div className="app-page">
      <div className="page-frame">
        <form className="surface-card form-card form-card--wide" onSubmit={submit}>
          <span className="section-tag">Inscription</span>
          <h2 className="mb-2">Creer un compte candidat</h2>
          <p className="text-muted mb-4">
            Renseignez vos informations personnelles. Une fois le compte cree, vous serez
            redirige vers le formulaire CV.
          </p>

          <div className="row">
            <div className="col-md-6">
              <label className="form-label">Prenom</label>
              <input className="form-control mb-3" placeholder="Ex: Ahmed" value={form.first_name} onChange={(event) => updateField("first_name", event.target.value)} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Nom</label>
              <input className="form-control mb-3" placeholder="Ex: Benali" value={form.last_name} onChange={(event) => updateField("last_name", event.target.value)} required />
            </div>
          </div>

          <label className="form-label">Adresse email</label>
          <input className="form-control mb-3" placeholder="Ex: ahmed@email.com" type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} required />

          <div className="row">
            <div className="col-md-6">
              <label className="form-label">Mot de passe</label>
              <input className="form-control mb-3" type="password" placeholder="Au moins 6 caracteres" value={form.password} onChange={(event) => updateField("password", event.target.value)} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Confirmer le mot de passe</label>
              <input className="form-control mb-3" type="password" placeholder="Retapez le mot de passe" value={form.confirm_password} onChange={(event) => updateField("confirm_password", event.target.value)} required />
            </div>
          </div>

          <label className="form-label">Titre professionnel</label>
          <input className="form-control mb-3" placeholder="Ex: Data Analyst, Developpeur web..." value={form.title} onChange={(event) => updateField("title", event.target.value)} />

          <div className="row">
            <div className="col-md-6">
              <label className="form-label">Localisation</label>
              <input className="form-control mb-3" placeholder="Ex: Casablanca" value={form.location} onChange={(event) => updateField("location", event.target.value)} />
            </div>
            <div className="col-md-6">
              <label className="form-label">Annees d'experience</label>
              <input className="form-control mb-3" type="number" min="0" placeholder="Ex: 2" value={form.experience_years} onChange={(event) => updateField("experience_years", event.target.value)} />
            </div>
          </div>

          <div className="row">
            <div className="col-md-6">
              <label className="form-label">Niveau d'etude</label>
              <input className="form-control mb-3" placeholder="Ex: Licence, Master..." value={form.education_level} onChange={(event) => updateField("education_level", event.target.value)} />
            </div>
            <div className="col-md-6">
              <label className="form-label">Telephone</label>
              <input className="form-control mb-3" placeholder="Ex: 0612345678" value={form.phone} onChange={(event) => updateField("phone", event.target.value)} />
            </div>
          </div>

          <label className="form-label">Lien LinkedIn</label>
          <input className="form-control mb-3" placeholder="Ex: https://linkedin.com/in/..." value={form.linkedin_url} onChange={(event) => updateField("linkedin_url", event.target.value)} />

          <label className="form-label">Presentation personnelle</label>
          <textarea className="form-control mb-2" rows="4" placeholder="Parlez brievement de votre parcours, vos objectifs ou votre domaine..." value={form.bio} onChange={(event) => updateField("bio", event.target.value)} />

          {message ? <p className="text-success small mb-2">{message}</p> : null}
          {error ? <p className="text-danger small mb-2">{error}</p> : null}

          <button className="btn btn-success w-100 mt-3" disabled={loading}>
            {loading ? "Creation..." : "Creer le compte"}
          </button>
        </form>
      </div>
    </div>
  );
}
