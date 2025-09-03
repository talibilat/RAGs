import React, { useState } from 'react';  // Import React and useState hook for state management
import axios from 'axios';  // Import axios for making HTTP requests

// FileUpload component accepts props: setLoading, loading, and loadingRef for controlling the loading state and bar
const FileUpload = ({ setLoading, loading, loadingRef }) => {
  const [file, setFile] = useState(null);  // State to store the selected file
  const [fileName, setFileName] = useState("");  // State to store the file name for display

  const backendUrl = "http://localhost:8000";  // URL for the backend API to handle file uploads

  // Handle file selection by the user
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];  // Get the first selected file
    if (selectedFile) {
      setFile(selectedFile);  // Store the selected file in state
      setFileName(selectedFile.name);  // Store the file name in state for display
    }
  };

  // Handle the file upload process
  const handleFileUpload = async () => {
    // If no file is selected, alert the user
    if (!file) {
      alert("Please select a file to upload.");
      return;
    }

    const formData = new FormData();  // Create a FormData object to send the file in the request
    formData.append("file", file);  // Append the file to the FormData object

    try {
      setLoading(true);  // Set loading state to true to show the loading bar
      loadingRef.current?.continuousStart();  // Start the loading bar if the ref is available

      // Send the file to the backend via a POST request
      const response = await axios.post(`${backendUrl}/upload/`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",  // Set content type for file upload
        },
      });

      // Alert the user on successful upload
      alert(`File uploaded successfully: ${response.data.filename}`);
    } catch (error) {
      // Log and alert the user if there's an error
      console.error("Error uploading file:", error);
      alert("Failed to upload the file.");
    } finally {
      setLoading(false);  // Reset loading state once the upload is complete
      loadingRef.current?.complete();  // Complete the loading bar
    }
  };

  return (
    <div className="side-menu-button">
      {/* Label for the file input */}
      <label htmlFor="file-upload" className="custom-file-upload">
        <span>+ </span> Upload New File
      </label>
      
      {/* Hidden file input field */}
      <input id="file-upload" type="file" style={{ display: 'none' }} onChange={handleFileChange} />
      
      {/* Button to trigger file upload, disabled during loading */}
      <button onClick={handleFileUpload} className="upload-button" disabled={loading}>
        {loading ? "Uploading..." : "Upload File"}  {/* Button label changes during loading */}
      </button>
      
      {/* Display the selected file name, if any */}
      {fileName && <p className="file-name-display">Selected File: {fileName}</p>}
    </div>
  );
};

export default FileUpload;  // Export the component for use in other parts of the application
