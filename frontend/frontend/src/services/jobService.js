export const getJobs = async () => {
  return {
    data: [
      { id: 1, title: "Data Scientist", company: "OCP", location: "Casablanca", score: 85 },
      { id: 2, title: "AI Engineer", company: "Capgemini", location: "Rabat", score: 78 },
      { id: 3, title: "Backend Developer", company: "Oracle", location: "Remote", score: 92 },
    ],
  };
};