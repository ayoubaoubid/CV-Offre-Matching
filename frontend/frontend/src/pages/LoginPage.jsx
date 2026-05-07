import { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import { loginUser } from "../services/authService";


export default function LoginPage() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await loginUser({
        email: email.trim(),
        password,
      });
      login({
        user: response.data.user,
        tokens: response.data.tokens,
      });
      navigate("/upload");
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          "Connexion impossible. Verifie l'email et le mot de passe."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell app-shell--auth">
      <section className="auth-hero">
        <div className="auth-hero__content">
          <span className="eyebrow">CV Offer Matching</span>
          <h1>Connectez-vous et completez votre candidature en quelques etapes.</h1>
          <p>
            Le candidat se connecte, ajoute son CV, renseigne ses skills et retrouve ensuite
            tout son profil dans un seul espace.
          </p>
          <div className="auth-demo">
            <div>
              <strong>Compte test candidat</strong>
              <span>candidate01@cvmatch.test</span>
              <span>Mot de passe: test1234</span>
            </div>
            <div>
              <strong>Compte test recruteur</strong>
              <span>admin.demo@cvmatch.test</span>
              <span>Mot de passe: admin123</span>
            </div>
          </div>
        </div>
      </section>

      <section className="auth-panel">
        <form className="surface-card auth-card" onSubmit={submit}>
          <span className="section-tag">Connexion</span>
          <h2 className="mb-2">Acceder a votre espace</h2>
          <p className="text-muted mb-4">
            Utilisez un email et un mot de passe existants dans la base pour entrer sans erreur.
          </p>

          <label className="form-label">Adresse email</label>
          <input
            className="form-control form-control-lg mb-3"
            type="email"
            placeholder="Ex: candidate01@cvmatch.test"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />

          <label className="form-label">Mot de passe</label>
          <input
            className="form-control form-control-lg mb-2"
            type="password"
            placeholder="Entrez votre mot de passe"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          {error ? <p className="text-danger small mb-3">{error}</p> : null}

          <button className="btn btn-primary btn-lg w-100" disabled={loading}>
            {loading ? "Connexion..." : "Se connecter"}
          </button>

          <button
            type="button"
            className="btn btn-link mt-3 px-0"
            onClick={() => navigate("/register")}
          >
            Creer un nouveau compte
          </button>
        </form>
      </section>
    </div>
  );
}
