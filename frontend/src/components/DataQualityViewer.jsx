import React from "react";
import "../App.css";

// ---------------------------------------------
// Generic Table Section
// ---------------------------------------------
const TableSection = ({ title, data }) => {
  const entries = Object.entries(data || {});

  if (!entries.length) {
    return (
      <div className="table-section">
        <h3>{title}</h3>
        <p className="empty-message">✔ No {title.toLowerCase()}.</p>
      </div>
    );
  }

  return (
    <div className="table-section">
      <h3>{title}</h3>

      <div className="scroll-table">
        <table className="dq-table">
          <thead>
            <tr>
              <th style={{ width: "40%" }}>Key</th>
              <th style={{ width: "60%" }}>Value</th>
            </tr>
          </thead>

          <tbody>
            {entries.map(([k, v], idx) => (
              <tr key={idx}>
                <td>{k}</td>
                <td>{JSON.stringify(v)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ---------------------------------------------
// Summary Statistics Table
// ---------------------------------------------
const SummaryTable = ({ stats }) => {
  if (!stats || Object.keys(stats).length === 0) {
    return (
      <div className="table-section">
        <h3>Summary Statistics</h3>
        <p className="empty-message">✔ No summary statistics available.</p>
      </div>
    );
  }

  const features = Object.keys(stats);
  const columns = ["count", "mean", "std", "min", "max"];

  return (
    <div className="table-section">
      <h3>Summary Statistics</h3>

      <div className="scroll-table">
        <table className="dq-table summary-table">
          <thead>
            <tr>
              <th className="sticky-left">Feature</th>
              {columns.map((col, i) => (
                <th key={i}>{col}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {features.map((feature, i) => (
              <tr key={i}>
                <td className="sticky-left">{feature}</td>
                {columns.map((col, j) => (
                  <td key={j}>
                    {stats[feature][col] !== undefined
                      ? stats[feature][col]
                      : "-"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
// Check if all values are zero in an object
const isAllZero = (obj) =>
  obj && Object.values(obj).every((v) => Number(v) === 0);


// ---- Category Inconsistencies Section ----
const CategorySection = ({ categoryData }) => {
  if (!categoryData || Object.keys(categoryData).length === 0) {
    return null;
  }

  return (
    <div className="table-section">
      <h3>Category Inconsistencies</h3>

      {Object.entries(categoryData).map(([colName, info]) => {
        const valid = info.valid_categories || [];
        const rows = info.rows || {};
        const entries = Object.entries(rows);

        return (
          <div key={colName} style={{ marginBottom: "18px", textAlign: "left" }}>
            <h4>{colName}</h4>

            {valid.length > 0 && (
              <p className="small-note">
                <strong>Valid categories:</strong> {valid.join(", ")}
              </p>
            )}

            {entries.length > 0 ? (
              <div className="scroll-table">
                <table className="dq-table">
                  <thead>
                    <tr>
                      <th style={{ width: "10%" }}>Row Index</th>
                      <th style={{ width: "25%" }}>Original</th>
                      <th style={{ width: "25%" }}>Suggested</th>
                      <th style={{ width: "10%" }}>Confidence</th>
                      <th style={{ width: "30%" }}>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map(([rowIdx, payload]) => (
                      <tr key={rowIdx}>
                        <td>{rowIdx}</td>
                        <td>{payload.original}</td>
                        <td>{payload.suggestion || "-"}</td>
                        <td>{payload.confidence || "-"}</td>
                        <td>{payload.reason || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="empty-message">
                ✔ No inconsistencies detected in <strong>{colName}</strong>.
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
};




const DataQualityViewer = ({ data }) => {
  return (

    <div className="dq-container">

      {isAllZero(data.missing_values) ? (
      <div className="table-section">
        <h3>Missing Values</h3>
        <p className="empty-message">✔ No missing values detected.</p>
      </div>
      ) : (
        <TableSection title="Missing Values" data={data.missing_values} />
      )}

      {isAllZero(data.outliers_detected) ? (
        <div className="table-section">
          <h3>Outliers Detected</h3>
          <p className="empty-message">✔ No outliers detected.</p>
        </div>
      ) : (
        <TableSection title="Outliers Detected" data={data.outliers_detected} />
      )}

      <TableSection title="Invalid Emails" data={data.invalid_format?.email} />
      <TableSection title="Invalid Dates" data={data.invalid_format?.date} />
      <TableSection title="Invalid Phone Numbers" data={data.invalid_format?.phone} />
      <TableSectionDuplicate title="Duplicate Rows" data={data.duplicate_rows} />

      <CategorySection categoryData={data.category_inconsistencies} />

      <SummaryTable stats={data.summary_statistics} />
    </div>
  );
};
const TableSectionDuplicate = ({ title, data }) => {
  const entries = Object.entries(data || {});

  if (!entries.length) {
    return (
      <div className="table-section">
        <h3>{title}</h3>
        <p className="empty-message">✔ No duplicate rows.</p>
      </div>
    );
  }

  return (
    <div className="table-section">
      <h3>{title}</h3>

      <div className="scroll-table">
        <table className="dq-table">
          <thead>
            <tr>
              <th style={{ width: "30%" }}>Row Indexes</th>
              <th style={{ width: "70%" }}>Example Row</th>
            </tr>
          </thead>

          <tbody>
            {entries.map(([group, obj], idx) => {
              const rows = obj.rows.join(", ");
              const example = Object.entries(obj.example)
                .map(([k, v]) => `${k}=${v}`)
                .join(",\n");

              return (
                <tr key={idx}>
                  <td>{rows}</td>
                  <td>{example}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataQualityViewer;
