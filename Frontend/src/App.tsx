import { useState } from "react";
import GraphView from "./GraphView.tsx";

export default function App() {
  const [seed, setSeed] = useState("");

  return (
    <div style={{ width: "100vw", height: "100vh", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: 12, borderBottom: "1px solid #eee", display: "flex", gap: 8 }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const data = new FormData(e.currentTarget as HTMLFormElement);
            setSeed((data.get("seed") as string) || "");
          }}
          style={{ display: "flex", gap: 8 }}
        >
          <input
            name="seed"
            placeholder="group.table (optional)"
            defaultValue={seed}
            style={{ padding: "8px 10px", minWidth: 280, borderRadius: 8, border: "1px solid #ccc" }}
          />
          <button
            type="submit"
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #ccc", background: "#fff" }}
          >
            Load
          </button>
        </form>
        <div style={{ marginLeft: "auto", opacity: 0.7 }}>API: {import.meta.env.VITE_API_BASE}</div>
      </div>
      <div style={{ flex: 1 }}>
        <GraphView seed={seed || undefined} />
      </div>
    </div>
  );
}
