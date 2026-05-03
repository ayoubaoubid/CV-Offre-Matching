import { useState } from "react";
import API from "../services/api";

export default function ProfileForm() {
  const [form, setForm] = useState({
    secteur: "",
    experience: "",
    education: "",
    localisation: "",
    competences: ""
  });

  const handleChange = (e) => {
    setForm({...form, [e.target.name]: e.target.value});
  };

  const submit = async () => {
    try {
      const res = await API.post("/match-jobs/", form);
      console.log(res.data);
      alert("Matching done !");
    } catch {
      alert("Error");
    }
  };

  return (
    <div className="container mt-4">

      <h2>🎯 Job Matching</h2>

      <input name="secteur" placeholder="Secteur" onChange={handleChange} className="form-control mt-2"/>
      <input name="experience" placeholder="Expérience" onChange={handleChange} className="form-control mt-2"/>
      <input name="education" placeholder="Niveau d'étude" onChange={handleChange} className="form-control mt-2"/>
      <input name="localisation" placeholder="Localisation" onChange={handleChange} className="form-control mt-2"/>

      <textarea name="competences" placeholder="Compétences (ex: Python, ML...)" onChange={handleChange} className="form-control mt-2"/>

      <button className="btn btn-primary mt-3" onClick={submit}>
        Match Jobs
      </button>

    </div>
  );
}