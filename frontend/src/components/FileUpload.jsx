import React, { useState } from "react";
import axios from "axios";

const API_BASE = "https://charulathag21-gen-ai-data-quality-helper.hf.space";

const FileUpload = ({ setReport }) => {
  const [file, setFile] = useState(null);

  const handleUpload = async () => {
    if (!file) {
      alert("Please upload a CSV file");
      return;
    }

    // 🔐 Get JWT token
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please login first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        `${API_BASE}/quality/report`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${token}`, 
          },
        }
      );

      setReport(response.data);
    } catch (error) {
      console.error("Upload error:", error);
      alert("Error uploading file. Check console for details.");
    }
  };

  return (
    <div className="upload-box">
      <input
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <button onClick={handleUpload}>Upload & Analyze</button>
    </div>
  );
};

export default FileUpload;
