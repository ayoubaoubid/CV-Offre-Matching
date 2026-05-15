import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import { fetchCurrentUser, updateCurrentUser } from "../services/authService";
import {getSavedJobs,saveJob,removeSavedJob,} from "../services/savedService";


function buildFormFromUser(user) {
  return {
    first_name: user?.first_name ?? "",
    last_name: user?.last_name ?? "",
    title: user?.profile?.title ?? "",
    bio: user?.profile?.bio ?? "",
    location: user?.profile?.location ?? "",
    experience_years: user?.profile?.experience_years ?? 0,
    education_level: user?.profile?.education_level ?? "",
    phone: user?.profile?.phone ?? "",
    linkedin_url: user?.profile?.linkedin_url ?? "",
    skills: (user?.skills ?? []).map((skill) => skill.name).join(", "),
    cv_text: user?.cv?.raw_text ?? "",
  };
}


export default function ProfilePage() {
  const { user, updateUser, authReady } = useContext(AuthContext);
  const navigate = useNavigate();
  const [form, setForm] = useState(buildFormFromUser(user));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [savedJobs, setSavedJobs] = useState([]);
  useEffect(() => {
    if (!authReady) {
      return;
    }

    if (!user) {
      navigate("/");
      return;
    }

    let isMounted = true;

    const loadProfile = async () => {
      setLoading(true);
      try {
        const response = await fetchCurrentUser();
        if (!isMounted) {
          return;
        }
        updateUser(response.data.user);
        setForm(buildFormFromUser(response.data.user));
        const saved = await getSavedJobs();
        setSavedJobs(saved.data);
      } catch {
        if (!isMounted) {
          return;
        }
        setError("Impossible de charger le profil.");
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
  }, [authReady, navigate, user?.id]);

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const toggleSaveJob = async (jobId, isSaved) => {
  try {
    if (isSaved) {
      await removeSavedJob(jobId);
      setSavedJobs((current) =>
        current.filter((job) => job.job_id !== jobId)
      );
    } else {
      await saveJob(jobId);

      const saved = await getSavedJobs();
      setSavedJobs(saved.data);
    }
  } catch {
    setError("Impossible de modifier les favoris.");
  }
};

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const response = await updateCurrentUser({
        ...form,
        experience_years: Number(form.experience_years || 0),
        skills: form.skills,
      });
      updateUser(response.data.user);
      setForm(buildFormFromUser(response.data.user));
      setMessage("Profil mis a jour avec succes.");
    } catch {
      setError("Impossible de sauvegarder le profil.");
    } finally {
      setSaving(false);
    }
  };

  if (!authReady || loading) {
    return <div className="page-frame py-5"><p>Chargement du profil...</p></div>;
  }

  return (
    <div className="app-page">
      <div className="page-frame page-frame--narrow">
        <div className="hero-strip mb-4">
          <div>
            <span className="section-tag">Profil</span>
            <h2 className="mb-1">Profil candidat</h2>
            <p className="text-muted mb-0">{user?.email}</p>
          </div>
          <button className="btn btn-outline-primary" onClick={() => navigate("/upload")}>
            Completer CV et skills
          </button>
        </div>

        <div className="row g-4">
          <div className="col-lg-5">
            <div className="surface-card info-card h-100">
              <h5>Informations enregistrees</h5>
              <p className="mb-2"><strong>Nom complet:</strong> {user?.first_name} {user?.last_name}</p>
              <p className="mb-2"><strong>Titre:</strong> {user?.profile?.title || "Non renseigne"}</p>
              <p className="mb-2"><strong>Localisation:</strong> {user?.profile?.location || "Non renseignee"}</p>
              <p className="mb-2"><strong>Experience:</strong> {user?.profile?.experience_years ?? 0} an(s)</p>
              <p className="mb-2"><strong>Etudes:</strong> {user?.profile?.education_level || "Non renseigne"}</p>
              <p className="mb-2"><strong>Telephone:</strong> {user?.profile?.phone || "Non renseigne"}</p>
              <p className="mb-2"><strong>LinkedIn:</strong> {user?.profile?.linkedin_url || "Non renseigne"}</p>
              <p className="mb-0"><strong>CV enregistre:</strong> {user?.cv?.raw_text ? "Oui" : "Non"}</p>
            </div>
          </div>

          <div className="col-lg-7">
            <div className="surface-card info-card h-100">
              <h5>Skills enregistres</h5>
              {(user?.skills ?? []).length ? (
                <div className="skill-cloud">
                  {user.skills.map((skill) => (
                    <span className="skill-pill" key={skill.id}>
                      {skill.name}
                      {skill.level ? ` - ${skill.level}` : ""}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mb-0 text-muted">Aucune skill enregistree pour le moment.</p>
              )}
            </div>
          </div>
        </div>

        <div className="surface-card info-card mt-4">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5 className="mb-0">Jobs sauvegardes</h5>
            <span className="badge bg-primary">
              {savedJobs.length}
            </span>
          </div>

          {savedJobs.length ? (
            <div className="row g-3">
              {savedJobs.map((job) => (
                <div className="col-md-6" key={job.id}>
                  <div className="job-card h-100">
                    <div className="d-flex justify-content-between align-items-start">
                      <div>
                        <h6 className="fw-bold mb-1">
                          {job.title}
                        </h6>

                        <p className="text-muted mb-1">
                          {job.company}
                        </p>

                        <p className="small mb-2">
                          📍 {job.location}
                        </p>
                      </div>

                      <button
                        className="btn btn-sm btn-outline-danger"
                        onClick={() => toggleSaveJob(job.job_id, true)}
                      >
                        Retirer
                      </button>
                    </div>

                    <div className="mt-3">
                      <small className="text-muted">
                        Sauvegarde le{" "}
                        {new Date(job.saved_at).toLocaleDateString()}
                      </small>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted mb-0">
              Aucun job sauvegarde.
            </p>
          )}
        </div>      
        <form className="surface-card form-card mt-4" onSubmit={submit}>
          <h5>Modifier mon profil</h5>

          <div className="row">
            <div className="col-md-6">
              <input className="form-control my-2" placeholder="Prenom" value={form.first_name} onChange={(event) => updateField("first_name", event.target.value)} />
            </div>
            <div className="col-md-6">
              <input className="form-control my-2" placeholder="Nom" value={form.last_name} onChange={(event) => updateField("last_name", event.target.value)} />
            </div>
          </div>

          <input className="form-control my-2" placeholder="Titre professionnel" value={form.title} onChange={(event) => updateField("title", event.target.value)} />
          <textarea className="form-control my-2" rows="3" placeholder="Presentation personnelle" value={form.bio} onChange={(event) => updateField("bio", event.target.value)} />

          <div className="row">
            <div className="col-md-6">
              <input className="form-control my-2" placeholder="Localisation" value={form.location} onChange={(event) => updateField("location", event.target.value)} />
            </div>
            <div className="col-md-6">
              <input className="form-control my-2" type="number" min="0" placeholder="Annees d'experience" value={form.experience_years} onChange={(event) => updateField("experience_years", event.target.value)} />
            </div>
          </div>

          <div className="row">
            <div className="col-md-6">
              <input className="form-control my-2" placeholder="Niveau d'etude" value={form.education_level} onChange={(event) => updateField("education_level", event.target.value)} />
            </div>
            <div className="col-md-6">
              <input className="form-control my-2" placeholder="Telephone" value={form.phone} onChange={(event) => updateField("phone", event.target.value)} />
            </div>
          </div>

          <input className="form-control my-2" placeholder="Lien LinkedIn" value={form.linkedin_url} onChange={(event) => updateField("linkedin_url", event.target.value)} />
          <textarea className="form-control my-2" rows="3" placeholder="Skills separees par virgule" value={form.skills} onChange={(event) => updateField("skills", event.target.value)} />
          <textarea className="form-control my-2" rows="6" placeholder="Texte du CV ou resume professionnel" value={form.cv_text} onChange={(event) => updateField("cv_text", event.target.value)} />

          {message ? <p className="text-success small mt-2 mb-0">{message}</p> : null}
          {error ? <p className="text-danger small mt-2 mb-0">{error}</p> : null}

          <button className="btn btn-primary mt-3 align-self-start" disabled={saving}>
            {saving ? "Sauvegarde..." : "Sauvegarder le profil"}
          </button>
        </form>
      </div>
    </div>
  );
}
