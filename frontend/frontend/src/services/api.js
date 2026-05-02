import axios from "axios"; // une librairie qui permet de faire des requêtes HTTP

// Création de l'instance Axios avec la configuration de base
const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// --- INTERCEPTEUR DE REQUÊTES ---
// S'exécute avant chaque requête envoyée au backend
API.interceptors.request.use(
  (config) => {
    // Si vous utilisez des tokens (JWT), décommentez les lignes suivantes plus tard :
    // const token = localStorage.getItem("access_token");
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// --- INTERCEPTEUR DE RÉPONSES ---
// S'exécute quand le backend répond, avant que votre composant (ex: App.jsx) ne reçoive les données
API.interceptors.response.use(
  (response) => {
    // Tout va bien (Status 2xx)
    return response;
  },
  (error) => {
    // Gestion globale des erreurs
    if (!error.response) {
      console.error("Erreur réseau : Le backend semble injoignable.");
    } else {
      const { status } = error.response;
      if (status === 401) {
        console.warn("Non autorisé ! Redirection vers la page de connexion...");
        // Exemple: window.location.href = '/';
      } else if (status === 404) {
        console.warn("Ressource introuvable !");
      } else if (status >= 500) {
        console.error("Erreur serveur côté Django !");
      }
    }
    return Promise.reject(error);
  }
);

export default API;