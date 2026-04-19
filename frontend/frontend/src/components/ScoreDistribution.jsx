import { BarChart, Bar, XAxis, YAxis } from "recharts";

export default function ScoreDistribution({ data }) {
  return (
    <BarChart width={400} height={300} data={data}>
      <XAxis dataKey="name" />
      <YAxis />
      <Bar dataKey="score" />
    </BarChart>
  );
}