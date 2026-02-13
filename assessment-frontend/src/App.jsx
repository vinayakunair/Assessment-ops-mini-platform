import { useState } from "react";
import Attempts from "./Attempts";
import Leaderboard from "./Leaderboard";

export default function App() {
  const [page, setPage] = useState("attempts");

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h1>Assessment Ops Mini Platform</h1>

      <button onClick={() => setPage("attempts")}>Attempts</button>
      <button onClick={() => setPage("leaderboard")} style={{ marginLeft: 10 }}>
        Leaderboard
      </button>

      <hr />

      {page === "attempts" && <Attempts />}
      {page === "leaderboard" && <Leaderboard />}
    </div>
  );
}
