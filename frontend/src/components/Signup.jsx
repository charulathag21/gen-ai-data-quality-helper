import React, { useState } from "react";
import axios from "axios";

const API_BASE = "https://charulathag21-gen-ai-data-quality-helper.hf.space";

const Signup = ({ switchMode }) => {
  const [form, setForm] = useState({
    username: "",
    password: "",
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSignup = async () => {
    try {
      await axios.post(
        `${API_BASE}/auth/register`,
        form
      );

      alert("Signup successful! Please login now.");

      // Switch to login screen
      if (switchMode) switchMode("login");

    } catch (err) {
      console.error(err);
      alert("Signup failed. Username may already exist.");
    }
  };

  return (
    <div className="auth-form">
      <input
        name="username"
        type="text"
        placeholder="Choose username"
        value={form.username}
        onChange={handleChange}
      />

      <input
        name="password"
        type="password"
        placeholder="Choose password"
        value={form.password}
        maxLength={50} 
        onChange={handleChange}
        />


      <button onClick={handleSignup}>Sign Up</button>
    </div>
  );
};

export default Signup;
