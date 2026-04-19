import { useState } from "react";
import { registerUser } from "../services/authService";
import { useNavigate } from "react-router-dom";

export default function RegisterPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const submit = async (e) => {
    e.preventDefault();
    await registerUser(form);
    alert("Account created!");
    navigate("/");
  };

  return (
    <div className="container mt-5 d-flex justify-content-center">
      <form className="card p-4 shadow" onSubmit={submit}>
        <h3>Register</h3>

        <input className="form-control my-2" placeholder="Email"
          onChange={(e) => setForm({ ...form, email: e.target.value })} />

        <input className="form-control my-2" type="password" placeholder="Password"
          onChange={(e) => setForm({ ...form, password: e.target.value })} />

        <button className="btn btn-success w-100">Register</button>
      </form>
    </div>
  );
}