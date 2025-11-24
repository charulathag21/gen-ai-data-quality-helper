import React from "react";
import { Link } from "react-router-dom";
import "./Home.css";

const Home = () => {
  return (
    <div className="home-container">
      <h1> Data Quality Helper</h1>

      <p className="home-desc">
        This tool automatically analyzes your dataset and detects:
      </p>

      <ul className="feature-list">
        <li>* Missing values</li>
        <li>* Outliers (IQR-based detection)</li>
        <li>* Duplicate rows</li>
        <li>* Invalid emails / dates / phone numbers</li>
        <li>* Category inconsistencies</li>
        <li>* Summary statistics (mean, std, min, max, …)</li>
        <li>* Cleaned dataset download</li>
        <li>* Visual charts for missing & outlier distributions</li>
      </ul>

      <p className="home-next">
        Upload your CSV to begin analyzing your dataset:
      </p>

      <Link to="/upload">
        <button className="start-btn"> Start Analysis</button>
      </Link>
    </div>
  );
};

export default Home;
