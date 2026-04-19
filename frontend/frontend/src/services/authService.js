export const loginUser = async (data) => {
  return {
    data: {
      user: { email: data.email },
      token: "fake-token",
    },
  };
};

export const registerUser = async (data) => {
  return {
    data: { message: "User created" },
  };
};