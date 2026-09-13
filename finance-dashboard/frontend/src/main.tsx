import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";

// One QueryClient for the whole app's lifetime — it holds the server-state
// cache TanStack Query maintains (ADR-0009). BrowserRouter makes the URL the
// source of truth for things like the selected month/account (also ADR-0009),
// ahead of any component that reads useSearchParams/useParams.
const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
