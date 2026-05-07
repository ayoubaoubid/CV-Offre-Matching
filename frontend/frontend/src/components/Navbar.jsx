import { useContext, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";


export default function Navbar() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const menuRef = useRef();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const initials = `${user?.first_name?.[0] ?? ""}${user?.last_name?.[0] ?? ""}`.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U";

  return (
    <nav className="app-navbar">
      <div className="page-frame page-frame--nav d-flex justify-content-between align-items-center">
        <div className="d-flex align-items-center gap-2 flex-wrap">
          <button className="btn btn-light btn-sm fw-bold shadow-sm" onClick={() => navigate(user ? "/dashboard" : "/")}>
            CV Matching
          </button>

          {user ? (
            <>
              <button className="btn btn-outline-light btn-sm" onClick={() => navigate("/results")}>
                Matching
              </button>
              <button className="btn btn-outline-light btn-sm" onClick={() => navigate("/upload")}>
                CV et Skills
              </button>
            </>
          ) : null}
        </div>

        <div className="position-relative" ref={menuRef}>
          {user ? (
            <>
              <div
                className="nav-avatar"
                onClick={() => setOpen((current) => !current)}
              >
                {initials}
              </div>

              {open ? (
                <div className="nav-menu">
                  <div className="px-3 py-2 border-bottom">
                    <div className="fw-bold">{user.first_name} {user.last_name}</div>
                    <div className="small text-muted">{user.email}</div>
                  </div>

                  <div style={menuItemStyle} onClick={() => {
                    navigate("/profile");
                    setOpen(false);
                  }}>
                    Profile
                  </div>

                  <div style={menuItemStyle} onClick={() => {
                    logout();
                    navigate("/");
                    setOpen(false);
                  }}>
                    Logout
                  </div>
                </div>
              ) : null}
            </>
          ) : (
            <button className="btn btn-primary btn-sm" onClick={() => navigate("/")}>
              Login
            </button>
          )}
        </div>
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
