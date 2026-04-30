import axios from "axios"; // une librairie qui permet de faire des requêtes HTTP

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
});

export default API;