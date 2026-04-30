export default function ProfilePage() {
  return (
    <div className="container mt-4">

      <h2>👤 Profile</h2>

      {/* CV INFO */}
      <div className="card p-3 mt-3">
        <h5>📄 CV Status</h5>
        <p>Uploaded CV: YES / NO</p>
      </div>

      {/* SKILLS */}
      <div className="card p-3 mt-3">
        <h5>🧠 Extracted Skills</h5>
        <ul>
          <li>Python</li>
          <li>Machine Learning</li>
          <li>Data Analysis</li>
        </ul>
      </div>

      {/* HISTORY */}
      <div className="card p-3 mt-3">
        <h5>📜 Search History</h5>
        <p>- Data Scientist jobs</p>
        <p>- AI Engineer Morocco</p>
      </div>

      

    </div>
  );
}