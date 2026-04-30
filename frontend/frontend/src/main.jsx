import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import "bootstrap/dist/css/bootstrap.min.css";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(  /** connecte React avec le HTML */ 
  <AuthProvider> {/** partager l’utilisateur (login) dans toute l’application */ }
    <App />
  </AuthProvider>
);