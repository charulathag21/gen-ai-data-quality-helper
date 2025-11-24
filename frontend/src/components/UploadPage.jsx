import React, { useState } from "react";
import FileUpload from "./FileUpload";
import Report from "./Report";
import Navbar from "./Navbar";

const UploadPage = () => {
  const [report, setReport] = useState(null);

  return (
    <>
      <Navbar />

      <div className="upload-page-container">
        <FileUpload setReport={setReport} />
        {report && <Report data={report} />}
      </div>
    </>
  );
};

export default UploadPage;
