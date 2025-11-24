import React, { useRef } from "react";
import html2canvas from "html2canvas";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

const Charts = ({ data }) => {
  const missingRef = useRef(null);
  const outlierRef = useRef(null);

  const missingChart = Object.entries(data.missing_values).map(([col, val]) => ({
    column: col,
    value: val,
  }));

  const outlierChart = Object.entries(data.outliers_detected).map(([col, val]) => ({
    column: col,
    value: val,
  }));

  // ----- FIX: DOWNLOAD PNG -----
  const downloadImage = async (ref, filename) => {
    if (!ref.current) return;

    const originalWidth = ref.current.style.width;
    ref.current.style.width = ref.current.scrollWidth + "px";

    const canvas = await html2canvas(ref.current, {
      backgroundColor: "#ffffff",
      scale: 2,
      useCORS: true
    });

    const link = document.createElement("a");
    link.download = filename;
    link.href = canvas.toDataURL("image/png");
    link.click();

    ref.current.style.width = originalWidth;
  };

  // ----- FIX: Dynamic chart width ensures last column is fully visible -----
  const calcWidth = (len) => Math.max(len * 120, 900);

  const boxStyle = {
    width: "100%",
    height: 400,
    overflowX: "auto",
    overflowY: "hidden",
    padding: "10px",
    border: "1px solid #ddd",
    borderRadius: "10px",
    background: "#fafafa",
    marginBottom: "40px"
  };

  return (
    <div style={{ width: "100%", marginTop: "30px" }}>

      <h3>
        Missing Values{" "}
        <button
          onClick={() => downloadImage(missingRef, "missing-values.png")}
          style={{
            marginLeft: "10px",
            padding: "4px 12px",
            cursor: "pointer",
            borderRadius: "4px",
            border: "1px solid #666",
            fontSize: "12px"
          }}
        >
          📥 Download PNG
        </button>
      </h3>
      

      {missingChart.every(item => Number(item.value) === 0) ? (
        <p className="empty-message">✔ No missing values chart available.</p>
      ) : (
      <div ref={missingRef} style={boxStyle}>
        <ResponsiveContainer width={calcWidth(missingChart.length)} height="100%">
          <BarChart
            data={missingChart}
            margin={{ top: 20, right: 20, left: 10, bottom: 80 }}
          >
            <XAxis
              dataKey="column"
              angle={45}
              textAnchor="start"
              interval={0}
              height={70}
            />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#4a90e2" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      )}

      <h3>
        Outliers{" "}
        <button
          onClick={() => downloadImage(outlierRef, "outliers.png")}
          style={{
            marginLeft: "10px",
            padding: "4px 12px",
            cursor: "pointer",
            borderRadius: "4px",
            border: "1px solid #666",
            fontSize: "12px"
          }}
        >
          📥 Download PNG
        </button>
      </h3>

      {outlierChart.every(item => Number(item.value) === 0) ? (
        <p className="empty-message">✔ No outliers chart available.</p>
      ) : (
      <div ref={outlierRef} style={boxStyle}>
        <ResponsiveContainer width={calcWidth(outlierChart.length)} height="100%">
          <BarChart
            data={outlierChart}
            margin={{ top: 20, right: 20, left: 10, bottom: 80 }}
          >
            <XAxis
              dataKey="column"
              angle={45}
              textAnchor="start"
              interval={0}
              height={70}
            />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#d64541" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      )}

    </div>
  );
};

export default Charts;
