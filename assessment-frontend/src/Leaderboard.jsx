import { useState } from "react";
import { api } from "./api";

export default function Leaderboard() {
  const [testName, setTestName] = useState("");
  const [rows, setRows] = useState([]);

  const load = async () => {
    const res = await api.get(`/api/leaderboard?test_name=${testName}`);
    setRows(res.data);
  };

  return (
    <div>
      <h2>Leaderboard</h2>

      <input
        placeholder="Test name (eg: JEE Mock 1)"
        value={testName}
        onChange={(e) => setTestName(e.target.value)}
      />
      <button onClick={load} style={{ marginLeft: 10 }}>
        Load
      </button>

      <table border="1" cellPadding="8" style={{ marginTop: 20 }}>
        <thead>
          <tr>
            <th>Name</th>
            <th>Score</th>
            <th>Accuracy</th>
            <th>Net Correct</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.student?.full_name}</td>
              <td>{r.score}</td>
              <td>{r.accuracy?.toFixed(2)}%</td>
              <td>{r.net_correct}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
