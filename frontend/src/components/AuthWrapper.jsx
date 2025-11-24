import React, { useState } from "react";
import Login from "./Login";
import Signup from "./Signup";
import "./Auth.css";

const AuthWrapper = () => {
  const [mode, setMode] = useState("login");

  return (
    <div className="auth-container">
      <h1 className="title">Data Cleaning Copilot</h1>

      <div className="auth-buttons">
        <button
          className={mode === "login" ? "active" : ""}
          onClick={() => setMode("login")}
        >
          Login
        </button>

        <button
          className={mode === "signup" ? "active" : ""}
          onClick={() => setMode("signup")}
        >
          Sign Up
        </button>
      </div>

      <div className="auth-box">
        {mode === "login" ? (
          <Login switchMode={setMode} />
        ) : (
          <Signup switchMode={setMode} />
        )}
      </div>
    </div>
  );
};

export default AuthWrapper;
