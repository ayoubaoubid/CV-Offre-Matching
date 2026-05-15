import { useContext, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import {
  createRecruiterJob,
  getRecruiterJob,
  updateRecruiterJob,
} from "../services/recruiterService";


const emptyForm = {
  title: "",
  company: "",
  sector: "",
  location: "",
  contract_type: "CDI",
  experience_required: 0,
  salary: "",
  status: "open",
  expires_at: "",
  description: "",
  skills: "",
};


function buildPayload(form) {
  return {
    ...form,
    experience_required: Number(form.experience_required || 0),
    expires_at: form.expires_at || null,
    skills: form.skills
      .split(",")
      .map((skill) => skill.trim())
      .filter(Boolean),
  };
}


function getSaveErrorMessage(requestError) {
  if (!requestError?.response) {
    return "Erreur reseau: le backend ne repond pas.";
  }

  const serverData = requestError.response.data;
  if (serverData?.message) {
    return serverData.message;
  }

  if (serverData && typeof serverData === "object") {
    const firstError = Object.entries(serverData)[0];
    if (firstError) {
      const [field, value] = firstError;
      const message = Array.isArray(value) ? value[0] : value;
      return `${field}: ${message}`;
    }
  }

  return `Erreur ${requestError.response.status}: impossible de sauvegarder l'offre.`;
}


export default function RecruiterJobFormPage() {
  const { user, authReady } = useContext(AuthContext);
  const { jobId } = useParams();
  const isEdit = Boolean(jobId);
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
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

    if (!isEdit) {
      return;
    }

    let isMounted = true;
    const loadJob = async () => {
      try {
        const response = await getRecruiterJob(jobId);
        const job = response.data;
        if (isMounted) {
          setForm({
            title: job.title,
            company: job.company,
            sector: job.sector,
            location: job.location,
            contract_type: job.contractType,
            experience_required: job.experienceRequired,
            salary: job.salary,
            status: job.status,
            expires_at: job.expiresAt || "",
            description: job.description,
            skills: job.requiredSkills.join(", "),
          });
        }
      } catch {
        if (isMounted) {
          setError("Impossible de charger cette offre.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadJob();
    return () => {
      isMounted = false;
    };
  }, [authReady, isEdit, jobId, navigate, user]);

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = buildPayload(form);
      if (isEdit) {
        await updateRecruiterJob(jobId, payload);
      } else {
        await createRecruiterJob(payload);
      }
      navigate("/recruiter/jobs");
    } catch (requestError) {
      setError(getSaveErrorMessage(requestError));
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
          <span className="section-tag">Offre</span>
          <h2 className="mb-4">{isEdit ? "Modifier l'offre" : "Creer une offre"}</h2>

          <input className="form-control my-2" placeholder="Titre" value={form.title} onChange={(event) => updateField("title", event.target.value)} required />
          <input className="form-control my-2" placeholder="Entreprise" value={form.company} onChange={(event) => updateField("company", event.target.value)} required />
          <textarea className="form-control my-2" rows="5" placeholder="Description" value={form.description} onChange={(event) => updateField("description", event.target.value)} required />

          <div className="row">
            <div className="col-md-6">
              <input className="form-control my-2" placeholder="Secteur" value={form.sector} onChange={(event) => updateField("sector", event.target.value)} />
            </div>
            <div className="col-md-6">
              <input className="form-control my-2" placeholder="Localisation" value={form.location} onChange={(event) => updateField("location", event.target.value)} />
            </div>
          </div>

          <div className="row">
            <div className="col-md-4">
              <select className="form-select my-2" value={form.contract_type} onChange={(event) => updateField("contract_type", event.target.value)}>
                <option value="CDI">CDI</option>
                <option value="CDD">CDD</option>
                <option value="Stage">Stage</option>
                <option value="Freelance">Freelance</option>
                <option value="Alternance">Alternance</option>
              </select>
            </div>
            <div className="col-md-4">
              <input className="form-control my-2" type="number" min="0" placeholder="Experience requise" value={form.experience_required} onChange={(event) => updateField("experience_required", event.target.value)} />
            </div>
            <div className="col-md-4">
              <input className="form-control my-2" placeholder="Salaire optionnel" value={form.salary} onChange={(event) => updateField("salary", event.target.value)} />
            </div>
          </div>

          <div className="row">
            <div className="col-md-6">
              <select className="form-select my-2" value={form.status} onChange={(event) => updateField("status", event.target.value)}>
                <option value="open">Active</option>
                <option value="draft">Brouillon</option>
                <option value="closed">Fermee</option>
              </select>
            </div>
            <div className="col-md-6">
              <input className="form-control my-2" type="date" value={form.expires_at || ""} onChange={(event) => updateField("expires_at", event.target.value)} />
            </div>
          </div>

          <textarea className="form-control my-2" rows="3" placeholder="Competences demandees separees par virgule" value={form.skills} onChange={(event) => updateField("skills", event.target.value)} />

          {error ? <p className="text-danger small mt-2">{error}</p> : null}
          <div className="d-flex gap-2 mt-3">
            <button className="btn btn-primary" disabled={saving}>
              {saving ? "Sauvegarde..." : "Sauvegarder"}
            </button>
            <button type="button" className="btn btn-outline-dark" onClick={() => navigate("/recruiter/jobs")}>
              Annuler
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
