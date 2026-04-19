import { useContext, useState, useRef, useEffect } from "react";
import { AuthContext } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const menuRef = useRef();

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <nav
      className="navbar navbar-dark px-3 d-flex justify-content-between"
      style={{ backgroundColor: "#003008" }}
    >

      {/* LEFT SIDE */}
      <div className="d-flex align-items-center gap-2">

        {/* Logo */}
        <button
          className="btn btn-light btn-sm fw-bold shadow-sm"
          onClick={() => navigate("/dashboard")}
        >
          💼 CV Matching
        </button>

        {/* 2 BUTTONS ONLY IF LOGGED IN */}
        {user && (
          <>

            <button
              className="btn btn-outline-light btn-sm"
              onClick={() => navigate("/results")}
            >
              Results
            </button>

            <button
              className="btn btn-outline-light btn-sm"
              onClick={() => navigate("/upload")}
            >
              Upload CV
            </button>
          </>
        )}
      </div>

      {/* RIGHT SIDE (USER MENU) */}
      <div className="position-relative" ref={menuRef}>

        {user ? (
          <>
            {/* CIRCLE USER */}
            <div
              onClick={() => setOpen(!open)}
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "50%",
                background: "#0d6efd",
                color: "white",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                fontWeight: "bold",
              }}
            >
              {user.email[0].toUpperCase()}
            </div>

            {/* DROPDOWN */}
            {open && (
              <div
                style={{
                  position: "absolute",
                  top: "55px",
                  right: 0,
                  background: "white",
                  borderRadius: "10px",
                  width: "160px",
                  boxShadow: "0 5px 15px rgba(0,0,0,0.2)",
                }}
              >
                <div
                  style={menuItemStyle}
                  onClick={() => {
                    navigate("/profile");
                    setOpen(false);
                  }}
                >
                  👤 Profile
                </div>

                <div
                  style={menuItemStyle}
                  onClick={() => {
                    logout();
                    navigate("/");
                  }}
                >
                  🚪 Logout
                </div>
              </div>
            )}
          </>
        ) : (
          <button
            className="btn btn-primary btn-sm"
            onClick={() => navigate("/")}
          >
            Login
          </button>
        )}
      </div>
    </nav>
  );
}

const menuItemStyle = {
  padding: "12px",
  cursor: "pointer",
  borderBottom: "1px solid #eee",
  color: "black",
};