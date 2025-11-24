import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const API_BASE = "https://gen-ai-data-quality-helper-backend.hf.space";

const Login = () => {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    username: "",
    password: "",
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleLogin = async () => {
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, form);

      if (res.data.token) {
        localStorage.setItem("token", res.data.token);
        alert("Login successful!");
        navigate("/home"); // redirect to home page
      }
    } catch (err) {
      console.error(err);
      alert("Invalid username or password");
    }
  };

  return (
    <div className="auth-form">
      <input
        name="username"
        type="text"
        placeholder="Username"
        value={form.username}
        onChange={handleChange}
      />

      <input
        name="password"
        type="password"
        placeholder="Password"
        value={form.password}
        onChange={handleChange}
      />

      <button onClick={handleLogin}>Login</button>
    </div>
  );
};

export default Login;
