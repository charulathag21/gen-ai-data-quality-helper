import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import AuthWrapper from "./components/AuthWrapper";
import Home from "./components/Home";
import UploadPage from "./components/UploadPage";
import ProtectedRoute from "./components/ProtectedRoute";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/" element={<AuthWrapper />} />

        {/* Protected */}
        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />

        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <UploadPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
