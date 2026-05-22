import { useState } from "react";

export function App(): JSX.Element {
  const [records] = useState<Array<{ id: string; status: string }>>([]);
  return (
    <div style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1>FlowDeck</h1>
      <p>Operations console over the FlowService gRPC backend.</p>
      <p>
        Records loaded: <strong>{records.length}</strong>
      </p>
      <p>
        See <a href="/api">/api</a> for the gRPC reflection endpoint.
      </p>
    </div>
  );
}
