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

const FIELD_LABELS = {
  first_name: "Prenom",
  last_name: "Nom",
  email: "Adresse email",
  password: "Mot de passe",
  confirm_password: "Confirmation du mot de passe",
  title: "Titre professionnel",
  location: "Localisation",
  experience_years: "Annees d'experience",
  education_level: "Niveau d'etude",
  phone: "Telephone",
  linkedin_url: "Lien LinkedIn",
  bio: "Presentation personnelle",
};


export default function RegisterPage() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const extractErrorPayload = (serverData) => {
    if (!serverData) {
      return {
        generalMessage: "Creation du compte impossible.",
        fieldMessages: {},
      };
    }

    if (typeof serverData === "string") {
      return {
        generalMessage: serverData,
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

    const priorityFields = [
      "confirm_password",
      "email",
      "first_name",
      "last_name",
      "password",
      "linkedin_url",
      "phone",
      "experience_years",
      "non_field_errors",
      "detail",
    ];

    for (const field of priorityFields) {
      if (fieldMessages[field]) {
        if (field === "non_field_errors" || field === "detail") {
          return {
            generalMessage: fieldMessages[field],
            fieldMessages,
          };
        }
        return {
          generalMessage: `${FIELD_LABELS[field] ?? field}: ${fieldMessages[field]}`,
          fieldMessages,
        };
      }
    }

    return {
      generalMessage: "Creation du compte impossible.",
      fieldMessages,
    };
  };

  const buildRequestDebugMessage = (requestError) => {
    if (!requestError?.response) {
      return "Erreur reseau: le backend ne repond pas ou l'API est inaccessible.";
    }

    const statusCode = requestError.response.status;
    const serverData = requestError.response.data;

    if (typeof serverData === "string" && serverData.trim()) {
      const condensed = serverData.replace(/\s+/g, " ").slice(0, 180);
      return `Erreur ${statusCode}: ${condensed}`;
    }

    return `Erreur ${statusCode}: le compte n'a pas pu etre cree.`;
  };

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    setFieldErrors({});

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
      localStorage.setItem("last_registered_email", response.data.user.email);
      setMessage("Compte cree avec succes. Vous pouvez maintenant ajouter votre CV.");
      setTimeout(() => navigate("/upload"), 800);
    } catch (requestError) {
      const { generalMessage, fieldMessages } = extractErrorPayload(requestError.response?.data);
      const hasDetailedMessage = generalMessage && generalMessage !== "Creation du compte impossible.";
      setError(hasDetailedMessage ? generalMessage : buildRequestDebugMessage(requestError));
      setFieldErrors(fieldMessages);
    } finally {
      setLoading(false);
    }
  };

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
              <input className={`form-control mb-3 ${fieldErrors.first_name ? "is-invalid" : ""}`} placeholder="Ex: Ahmed" value={form.first_name} onChange={(event) => updateField("first_name", event.target.value)} required />
              {fieldErrors.first_name ? <p className="text-danger small mt-n2 mb-2">{fieldErrors.first_name}</p> : null}
            </div>
            <div className="col-md-6">
              <label className="form-label">Nom</label>
              <input className={`form-control mb-3 ${fieldErrors.last_name ? "is-invalid" : ""}`} placeholder="Ex: Benali" value={form.last_name} onChange={(event) => updateField("last_name", event.target.value)} required />
              {fieldErrors.last_name ? <p className="text-danger small mt-n2 mb-2">{fieldErrors.last_name}</p> : null}
            </div>
          </div>

          <label className="form-label">Adresse email</label>
          <input className={`form-control mb-3 ${fieldErrors.email ? "is-invalid" : ""}`} placeholder="Ex: ahmed@email.com" type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} required />
          {fieldErrors.email ? <p className="text-danger small mt-n2 mb-2">{fieldErrors.email}</p> : null}

          <div className="row">
            <div className="col-md-6">
              <label className="form-label">Mot de passe</label>
              <input className={`form-control mb-3 ${fieldErrors.password ? "is-invalid" : ""}`} type="password" placeholder="Au moins 6 caracteres" value={form.password} onChange={(event) => updateField("password", event.target.value)} required />
              {fieldErrors.password ? <p className="text-danger small mt-n2 mb-2">{fieldErrors.password}</p> : null}
            </div>
            <div className="col-md-6">
              <label className="form-label">Confirmer le mot de passe</label>
              <input className={`form-control mb-3 ${fieldErrors.confirm_password ? "is-invalid" : ""}`} type="password" placeholder="Retapez le mot de passe" value={form.confirm_password} onChange={(event) => updateField("confirm_password", event.target.value)} required />
              {fieldErrors.confirm_password ? <p className="text-danger small mt-n2 mb-2">{fieldErrors.confirm_password}</p> : null}
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
              <input className={`form-control mb-3 ${fieldErrors.experience_years ? "is-invalid" : ""}`} type="number" min="0" placeholder="Ex: 2" value={form.experience_years} onChange={(event) => updateField("experience_years", event.target.value)} />
              {fieldErrors.experience_years ? <p className="text-danger small mt-n2 mb-2">{fieldErrors.experience_years}</p> : null}
            </div>
          </div>

          <div className="row">
            <div className="col-md-6">
              <label className="form-label">Niveau d'etude</label>
              <input className="form-control mb-3" placeholder="Ex: Licence, Master..." value={form.education_level} onChange={(event) => updateField("education_level", event.target.value)} />
            </div>
            <div className="col-md-6">
              <label className="form-label">Telephone</label>
              <input className={`form-control mb-3 ${fieldErrors.phone ? "is-invalid" : ""}`} placeholder="Ex: 0612345678" value={form.phone} onChange={(event) => updateField("phone", event.target.value)} />
              {fieldErrors.phone ? <p className="text-danger small mt-n2 mb-2">{fieldErrors.phone}</p> : null}
            </div>
          </div>

          <label className="form-label">Lien LinkedIn</label>
          <input className={`form-control mb-3 ${fieldErrors.linkedin_url ? "is-invalid" : ""}`} placeholder="Ex: linkedin.com/in/mon-profil" value={form.linkedin_url} onChange={(event) => updateField("linkedin_url", event.target.value)} />
          {fieldErrors.linkedin_url ? <p className="text-danger small mt-n2 mb-2">{fieldErrors.linkedin_url}</p> : null}

          <label className="form-label">Presentation personnelle</label>
          <textarea className={`form-control mb-2 ${fieldErrors.bio ? "is-invalid" : ""}`} rows="4" placeholder="Parlez brievement de votre parcours, vos objectifs ou votre domaine..." value={form.bio} onChange={(event) => updateField("bio", event.target.value)} />
          {fieldErrors.bio ? <p className="text-danger small mt-2 mb-2">{fieldErrors.bio}</p> : null}

          {message ? <p className="text-success small mb-2">{message}</p> : null}
          {error ? <p className="text-danger small mb-2">{error}</p> : null}
          {Object.keys(fieldErrors).length ? (
            <div className="small mt-2 mb-2">
              <strong>Champs non valides :</strong>
              {Object.entries(fieldErrors).map(([field, fieldMessage]) => (
                <p className="text-danger mb-1" key={field}>
                  {FIELD_LABELS[field] ?? field}: {fieldMessage}
                </p>
              ))}
            </div>
          ) : null}

          <button className="btn btn-success w-100 mt-3" disabled={loading}>
            {loading ? "Creation..." : "Creer le compte"}
          </button>
        </form>
      </div>
    </div>
  );
}
