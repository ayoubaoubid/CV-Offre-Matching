import { createContext, useState } from "react";

export const AuthContext = createContext(); // Crée un contexte pour l'authentification

export const AuthProvider = ({ children }) => { // Composant fournisseur pour le contexte d'authentification
  const [user, setUser] = useState(null); // État pour stocker les informations de l'utilisateur connecté

  const login = (data) => setUser(data.user); // Fonction pour connecter un utilisateur en mettant à jour l'état avec les données de l'utilisateur
  const logout = () => setUser(null); // Fonction pour deconnecter un utilisateur en réinitialisant l'état à null

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children} 
    </AuthContext.Provider>
  );
};