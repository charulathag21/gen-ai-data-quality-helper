import React from "react";
import Charts from "./Charts.jsx";
import DataQualityViewer from "./DataQualityViewer.jsx";

const API_BASE = "https://charulathag21-gen-ai-data-quality-helper.hf.space";

const Report = ({ data }) => {

  // Download JSON file
  const downloadJSON = () => {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "data_quality_report.json";
    link.click();

    URL.revokeObjectURL(url);
  };

  // Check if all values are zero in an object
  const isAllZero = (obj) =>
    obj && Object.values(obj).every((v) => Number(v) === 0);

  return (
  <div className="report-container">
    <h2>📝 Data Quality Report</h2>

    <div className="report-content">
      <DataQualityViewer data={data} />
    </div>

    {(!isAllZero(data.missing_values) || !isAllZero(data.outliers_detected)) && (
      <>
        <h3>📊 Charts</h3>
        <Charts data={data} />
      </>
    )}

    <h3>⬇ Download Cleaned File</h3>
    <a href={`${API_BASE}${data.cleaned_file_download}`} download>
      <button>Download Cleaned CSV</button>
    </a>


    <h3>⬇ Developer JSON Report</h3>
    <button onClick={downloadJSON}>Download JSON Report</button>
  </div>
);

};

export default Report;
