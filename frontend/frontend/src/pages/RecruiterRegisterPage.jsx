import { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import { registerRecruiter } from "../services/authService";


const initialForm = {
  first_name: "",
  last_name: "",
  email: "",
  password: "",
  confirm_password: "",
  company_name: "",
  sector: "",
  location: "",
  professional_email: "",
  phone: "",
  website: "",
  logo_url: "",
  description: "",
};

const FIELD_LABELS = {
  first_name: "Prenom",
  last_name: "Nom",
  email: "Adresse email",
  password: "Mot de passe",
  confirm_password: "Confirmation du mot de passe",
  company_name: "Nom de l'entreprise",
  sector: "Secteur",
  location: "Localisation",
  professional_email: "Email professionnel",
  phone: "Telephone",
  website: "Site web",
  logo_url: "Logo",
  description: "Description",
};


export default function RecruiterRegisterPage() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
    setFieldErrors((current) => {
      if (!current[field]) {
        return current;
      }
      const next = { ...current };
      delete next[field];
      return next;
    });
  };

  const readServerErrors = (serverData) => {
    if (!serverData || typeof serverData === "string") {
      return {
        generalMessage: serverData || "Creation du compte recruteur impossible.",
        fieldMessages: {},
      };
    }

    const fieldMessages = {};
    for (const [field, value] of Object.entries(serverData)) {
      if (Array.isArray(value) && value.length) {
        fieldMessages[field] = String(value[0]);
      } else if (typeof value === "string" && value.trim()) {
        fieldMessages[field] = value;
      }
    }

    const firstField = Object.keys(fieldMessages)[0];
    return {
      generalMessage: firstField
        ? `${FIELD_LABELS[firstField] ?? firstField}: ${fieldMessages[firstField]}`
        : "Creation du compte recruteur impossible.",
      fieldMessages,
    };
  };

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setFieldErrors({});

    try {
      const response = await registerRecruiter(form);
      login({
        user: response.data.user,
        tokens: response.data.tokens,
      });
      localStorage.setItem("last_registered_email", response.data.user.email);
      navigate("/recruiter");
    } catch (requestError) {
      const { generalMessage, fieldMessages } = readServerErrors(requestError.response?.data);
      setError(
        requestError.response
          ? generalMessage
          : "Erreur reseau: le backend ne repond pas."
      );
      setFieldErrors(fieldMessages);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-page">
      <div className="page-frame">
        <form className="surface-card form-card form-card--wide" onSubmit={submit}>
          <span className="section-tag">Inscription recruteur</span>
          <h2 className="mb-2">Creer un compte recruteur</h2>
          <p className="text-muted mb-4">
            Creez votre espace entreprise pour publier des offres et suivre les candidatures.
          </p>

          <div className="row">
            <div className="col-md-6">
              <label className="form-label">Prenom</label>
              <input className={`form-control mb-3 ${fieldErrors.first_name ? "is-invalid" : ""}`} value={form.first_name} onChange={(event) => updateField("first_name", event.target.value)} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Nom</label>
              <input className={`form-control mb-3 ${fieldErrors.last_name ? "is-invalid" : ""}`} value={form.last_name} onChange={(event) => updateField("last_name", event.target.value)} required />
            </div>
          </div>

          <label className="form-label">Adresse email</label>
          <input className={`form-control mb-3 ${fieldErrors.email ? "is-invalid" : ""}`} type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} required />

          <div className="row">
            <div className="col-md-6">
              <label className="form-label">Mot de passe</label>
              <input className={`form-control mb-3 ${fieldErrors.password ? "is-invalid" : ""}`} type="password" value={form.password} onChange={(event) => updateField("password", event.target.value)} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Confirmer le mot de passe</label>
              <input className={`form-control mb-3 ${fieldErrors.confirm_password ? "is-invalid" : ""}`} type="password" value={form.confirm_password} onChange={(event) => updateField("confirm_password", event.target.value)} required />
            </div>
          </div>

          <label className="form-label">Nom de l'entreprise</label>
          <input className={`form-control mb-3 ${fieldErrors.company_name ? "is-invalid" : ""}`} value={form.company_name} onChange={(event) => updateField("company_name", event.target.value)} required />

          <div className="row">
            <div className="col-md-6">
              <label className="form-label">Secteur</label>
              <input className="form-control mb-3" placeholder="Ex: IT, Finance, Industrie" value={form.sector} onChange={(event) => updateField("sector", event.target.value)} />
            </div>
            <div className="col-md-6">
              <label className="form-label">Localisation</label>
              <input className="form-control mb-3" placeholder="Ex: Casablanca" value={form.location} onChange={(event) => updateField("location", event.target.value)} />
            </div>
          </div>

          <div className="row">
            <div className="col-md-6">
              <label className="form-label">Email professionnel</label>
              <input className={`form-control mb-3 ${fieldErrors.professional_email ? "is-invalid" : ""}`} type="email" value={form.professional_email} onChange={(event) => updateField("professional_email", event.target.value)} />
            </div>
            <div className="col-md-6">
              <label className="form-label">Telephone</label>
              <input className="form-control mb-3" value={form.phone} onChange={(event) => updateField("phone", event.target.value)} />
            </div>
          </div>

          <label className="form-label">Site web</label>
          <input className={`form-control mb-3 ${fieldErrors.website ? "is-invalid" : ""}`} placeholder="Ex: entreprise.com" value={form.website} onChange={(event) => updateField("website", event.target.value)} />

          <label className="form-label">URL du logo</label>
          <input className={`form-control mb-3 ${fieldErrors.logo_url ? "is-invalid" : ""}`} value={form.logo_url} onChange={(event) => updateField("logo_url", event.target.value)} />

          <label className="form-label">Description entreprise</label>
          <textarea className="form-control mb-2" rows="4" value={form.description} onChange={(event) => updateField("description", event.target.value)} />

          {error ? <p className="text-danger small mb-2">{error}</p> : null}
          {Object.entries(fieldErrors).map(([field, fieldMessage]) => (
            <p className="text-danger small mb-1" key={field}>
              {FIELD_LABELS[field] ?? field}: {fieldMessage}
            </p>
          ))}

          <button className="btn btn-success w-100 mt-3" disabled={loading}>
            {loading ? "Creation..." : "Creer le compte recruteur"}
          </button>

          <button type="button" className="btn btn-link mt-3 px-0" onClick={() => navigate("/")}>
            J'ai deja un compte recruteur
          </button>
        </form>
      </div>
    </div>
  );
}
