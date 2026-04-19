export default function WordCloud({ words }) {
  return (
    <div>
      {words.map((w, i) => (
        <span key={i} style={{ margin: "5px" }}>
          {w}
        </span>
      ))}
    </div>
  );
}