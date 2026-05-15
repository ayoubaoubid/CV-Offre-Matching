import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import {
  getCompanyProfile,
  updateCompanyProfile,
} from "../services/recruiterService";


const emptyProfile = {
  company_name: "",
  sector: "",
  description: "",
  website: "",
  location: "",
  logo_url: "",
  professional_email: "",
  phone: "",
};


export default function CompanyProfilePage() {
  const { user, authReady, updateUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyProfile);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authReady) {
      return;
    }
    if (!user) {
      navigate("/");
      return;
    }
    if (user.role !== "admin") {
      navigate("/dashboard");
      return;
    }

    let isMounted = true;
    const loadProfile = async () => {
      try {
        const response = await getCompanyProfile();
        if (isMounted) {
          setForm({ ...emptyProfile, ...response.data.company_profile });
        }
      } catch {
        if (isMounted) {
          setError("Impossible de charger le profil entreprise.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadProfile();
    return () => {
      isMounted = false;
    };
  }, [authReady, navigate, user]);

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const response = await updateCompanyProfile(form);
      if (response.data.user) {
        updateUser(response.data.user);
      }
      setMessage("Profil entreprise mis a jour.");
    } catch {
      setError("Impossible de sauvegarder le profil entreprise.");
    } finally {
      setSaving(false);
    }
  };

  if (!authReady || loading) {
    return <div className="page-frame py-5"><p>Chargement...</p></div>;
  }

  return (
    <div className="app-page">
      <div className="page-frame page-frame--narrow">
        <form className="surface-card form-card" onSubmit={submit}>
          <span className="section-tag">Entreprise</span>
          <h2 className="mb-4">Profil entreprise</h2>

          <input className="form-control my-2" placeholder="Nom de l'entreprise" value={form.company_name} onChange={(event) => updateField("company_name", event.target.value)} />
          <input className="form-control my-2" placeholder="Secteur" value={form.sector} onChange={(event) => updateField("sector", event.target.value)} />
          <textarea className="form-control my-2" rows="5" placeholder="Description de l'entreprise" value={form.description} onChange={(event) => updateField("description", event.target.value)} />

          <div className="row">
            <div className="col-md-6">
              <input className="form-control my-2" placeholder="Site web" value={form.website} onChange={(event) => updateField("website", event.target.value)} />
            </div>
            <div className="col-md-6">
              <input className="form-control my-2" placeholder="Localisation" value={form.location} onChange={(event) => updateField("location", event.target.value)} />
            </div>
          </div>

          <input className="form-control my-2" placeholder="URL du logo" value={form.logo_url} onChange={(event) => updateField("logo_url", event.target.value)} />
          <div className="row">
            <div className="col-md-6">
              <input className="form-control my-2" type="email" placeholder="Email professionnel" value={form.professional_email} onChange={(event) => updateField("professional_email", event.target.value)} />
            </div>
            <div className="col-md-6">
              <input className="form-control my-2" placeholder="Telephone" value={form.phone} onChange={(event) => updateField("phone", event.target.value)} />
            </div>
          </div>

          {message ? <p className="text-success small mt-2">{message}</p> : null}
          {error ? <p className="text-danger small mt-2">{error}</p> : null}
          <button className="btn btn-primary mt-3" disabled={saving}>
            {saving ? "Sauvegarde..." : "Sauvegarder"}
          </button>
        </form>
      </div>
    </div>
  );
}
