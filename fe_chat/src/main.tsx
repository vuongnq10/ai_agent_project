import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import AppStream from "./AppStream.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppStream />
  </StrictMode>
);
