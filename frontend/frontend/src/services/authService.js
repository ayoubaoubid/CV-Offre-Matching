import API from "./api";

export async function loginUser(data) {
  const response = await API.post("/users/login/", data);
  return response;
}

export async function registerUser(data) {
  const response = await API.post("/users/register/", data);
  return response;
}

export async function fetchCurrentUser() {
  const response = await API.get("/users/me/");
  return response;
}

export async function updateCurrentUser(data) {
  const response = await API.put("/users/me/", data);
  return response;
}
