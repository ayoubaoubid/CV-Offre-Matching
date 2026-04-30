import { useState, useContext } from "react";
import { loginUser } from "../services/authService";
import { AuthContext } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = async (e) => {
    e.preventDefault(); // rechargement du formulaire
    const res = await loginUser({ email, password });
    login(res.data);
    navigate("/dashboard");
  };

  return (
    <div className="container mt-5 d-flex justify-content-center">
      <form className="card p-4 shadow" onSubmit={submit}>
        <h3>Login</h3>

        <input className="form-control my-2" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
        <input className="form-control my-2" type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />

        <button className="btn btn-primary w-100">Login</button>

        <p className="text-primary mt-2" onClick={() => navigate("/register")} style={{ cursor: "pointer" }}>
          Create account
        </p>
      </form>
    </div>
  );
}