import React from "react";
import { useNavigate, Link } from "react-router-dom";

const Navbar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  return (
    <nav
      style={{
        width: "100%",
        background: "#007bff",
        padding: "12px 20px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        color: "white",
      }}
    >
      <Link to="/home" style={{ color: "white", textDecoration: "none", fontSize: "20px", fontWeight: "600" }}>
        Data Cleaning Copilot
      </Link>

      <button
        onClick={handleLogout}
        style={{
          background: "white",
          color: "#3e658eff",
          border: "none",
          padding: "6px 12px",
          borderRadius: "6px",
          fontWeight: "bold",
          cursor: "pointer",
        }}
      >
        Logout
      </button>
    </nav>
  );
};

export default Navbar;
