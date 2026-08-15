import React from "react";
import ReactDOM from "react-dom/client";
import { ThemeProvider } from "./hooks/useTheme";
import { Toaster } from "./components/ui/Toast";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
      <Toaster />
    </ThemeProvider>
  </React.StrictMode>,
);