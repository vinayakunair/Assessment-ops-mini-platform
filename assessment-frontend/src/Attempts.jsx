import { useEffect, useState } from "react";
import { api } from "./api";

export default function Attempts() {
  const [attempts, setAttempts] = useState([]);

  const load = async () => {
    const res = await api.get("/api/attempts?limit=20");
    setAttempts(res.data);
  };

  useEffect(() => {
    load();
  }, []);

  const recompute = async (id) => {
    await api.post(`/api/attempts/${id}/recompute`);
    alert("Recomputed!");
    load();
  };

  return (
    <div>
      <h2>Attempts</h2>
      <table border="1" cellPadding="8">
        <thead>
          <tr>
            <th>Source Event ID</th>
            <th>Status</th>
            <th>Duplicate Of</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {attempts.map((a) => (
            <tr key={a.id}>
              <td>{a.source_event_id}</td>
              <td>{a.status}</td>
              <td>{a.duplicate_of_attempt_id || "-"}</td>
              <td>
                <button onClick={() => recompute(a.id)}>Recompute</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
