import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  return (
    <nav className="navbar navbar-dark bg-dark px-3">
      <span className="navbar-brand" onClick={() => navigate("/dashboard")}>
        💼 CV Matching
      </span>

      <div>
        {user ? (
          <>
            <span className="text-white me-3">{user.email}</span>
            <button className="btn btn-danger btn-sm" onClick={logout}>
              Logout
            </button>
          </>
        ) : (
          <button className="btn btn-primary btn-sm" onClick={() => navigate("/")}>
            Login
          </button>
        )}
      </div>
    </nav>
  );
}