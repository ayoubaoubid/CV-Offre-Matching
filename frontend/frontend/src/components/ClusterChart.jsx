import { ScatterChart, Scatter, XAxis, YAxis } from "recharts";

export default function ClusterChart({ data }) {
  return (
    <ScatterChart width={400} height={300}>
      <XAxis dataKey="x" />
      <YAxis dataKey="y" />
      <Scatter data={data} />
    </ScatterChart>
  );
}