import { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import { updateCurrentUser } from "../services/authService";


export default function CVUploader() {
  const { user, updateUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [skills, setSkills] = useState((user?.skills ?? []).map((skill) => skill.name).join(", "));
  const [cvText, setCvText] = useState(user?.cv?.raw_text ?? "");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    setError("");

    try {
      const response = await updateCurrentUser({
        skills,
        cv_text: cvText,
      });
      updateUser(response.data.user);
      setMessage("Les informations du CV et les skills ont ete enregistrees.");
    } catch {
      setError("Impossible d'enregistrer les informations.");
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="page-frame py-5">
        <p className="text-danger">Connecte-toi d'abord pour enregistrer ton CV et tes skills.</p>
        <button className="btn btn-primary" onClick={() => navigate("/")}>
          Aller a la connexion
        </button>
      </div>
    );
  }

  return (
    <div className="app-page">
      <div className="page-frame page-frame--narrow">
        <div className="hero-strip mb-4">
          <div>
            <span className="section-tag">Etape 2</span>
            <h2 className="mb-1">CV et skills</h2>
            <p className="text-muted mb-0">
              Complete ton CV avec un formulaire simple. Les informations seront rattachees a ton compte.
            </p>
          </div>
          <button className="btn btn-outline-secondary" onClick={() => navigate("/profile")}>
            Retour au profil
          </button>
        </div>

        <form className="surface-card form-card" onSubmit={submit}>
          <label className="form-label">Skills</label>
          <textarea
            className="form-control mb-3"
            rows="3"
            placeholder="Exemple: Python, SQL, Machine Learning, Power BI"
            value={skills}
            onChange={(event) => setSkills(event.target.value)}
          />

          <label className="form-label">Texte du CV / resume professionnel</label>
          <textarea
            className="form-control"
            rows="10"
            placeholder="Collez ici le contenu du CV, vos experiences, vos formations et vos realisations..."
            value={cvText}
            onChange={(event) => setCvText(event.target.value)}
          />

          {message ? <p className="text-success mt-3 mb-0">{message}</p> : null}
          {error ? <p className="text-danger mt-3 mb-0">{error}</p> : null}

          <div className="d-flex gap-3 mt-4 flex-wrap">
            <button className="btn btn-primary" disabled={loading}>
              {loading ? "Enregistrement..." : "Enregistrer"}
            </button>
            <button type="button" className="btn btn-outline-dark" onClick={() => navigate("/dashboard")}>
              Voir les offres
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
