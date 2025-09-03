import React, { useState, useRef } from 'react';  // Import necessary hooks from React
import './styles/App.css';  // Import the main CSS for the application
import './styles/normal.css';  // Import additional CSS for normalization or other styling
import FileUpload from './components/FileUpload';  // Import the FileUpload component
import ChatBox from './components/ChatBox';  // Import the ChatBox component
import Logo from './components/Logo';  // Import the Logo component
import TopLoadingBar from './components/LoadingBar';  // Import the loading bar component

function App() {
  // State to store the user's query/message
  const [userMessage, setUserMessage] = useState(""); 
 

  // State to store the AI's response
  const [aiMessage, setAiMessage] = useState("");      

  // State to handle loading status, used to show or hide the loading bar
  const [loading, setLoading] = useState(false);       

  // Reference to the loading bar, allows us to control it programmatically
  const loadingRef = useRef(null);                     
 console.log('userMessage', userMessage);
  return (
    <div className="App">
      {/* The loading bar, appears at the top of the screen during loading */}
      <TopLoadingBar color="#f11946" ref={loadingRef} />  
      
      {/* Sidebar section containing the logo and the file upload functionality */}
      <aside className="sidemenu">
        <div className="logo-section">
          <Logo />  {/* Display the logo for the application */}
          <h1 className="company-name">Factor Law</h1>  {/* Company name */}
        </div>

        {/* File upload component, passes loading state and reference for controlling loading */}
        <FileUpload setLoading={setLoading} loadingRef={loadingRef} />
      </aside>

      {/* Chat box for displaying user messages and AI responses */}
      <ChatBox
        userMessage={userMessage}  // Pass the user's message to the ChatBox
        setUserMessage={setUserMessage}  // Function to update the user's message
        aiMessage={aiMessage}  // Pass the AI's response to the ChatBox
        setAiMessage={setAiMessage}  // Function to update the AI's response
        loading={loading}  // Current loading state
        setLoading={setLoading}  // Function to update the loading state
        loadingRef={loadingRef}  // Reference for controlling the loading bar
      />
    </div>
  );
}

export default App;  // Export the App component as the default export


























// import React, { useState, useRef } from 'react';
// import axios from 'axios';
// import LoadingBar from 'react-top-loading-bar';
// import './App.css';
// import './normal.css';
// import { marked } from 'marked';  // Import markdown parser


// function App() {
//   const [file, setFile] = useState(null);            // For file uploads
//   const [fileName, setFileName] = useState('');      // Store selected file name
//   const [query, setQuery] = useState("");            // For the user's query
//   const [userMessage, setUserMessage] = useState(""); // To display user's query in chat
//   const [aiMessage, setAiMessage] = useState("");     // To display AI's response in chat
//   const [loading, setLoading] = useState(false);      // Loading state for API requests
//   const loadingRef = useRef(null);                    // Reference to the loading bar


//   // Logo
//   const Logo = () => (
//     <svg
//       xmlns="http://www.w3.org/2000/svg"
//       width="40"
//       height="40"
//       viewBox="0 0 200 200"
//     >
//       {/* Red Circle */}
//       <circle cx="100" cy="100" r="100" fill="#C4161C" />
  
//       {/* White Dots */}
//       <circle cx="70" cy="60" r="12" fill="#ffffff" />
//       <circle cx="100" cy="60" r="12" fill="#ffffff" />
//       <circle cx="130" cy="60" r="12" fill="#ffffff" />
//       <circle cx="70" cy="100" r="12" fill="#ffffff" />
//       <circle cx="100" cy="100" r="12" fill="#ffffff" />
//       <circle cx="70" cy="140" r="12" fill="#ffffff" />
//     </svg>
//   );



//   // Handle file selection
//   const handleFileChange = (event) => {
//     const selectedFile = event.target.files[0];
//     if (selectedFile) {
//       setFile(selectedFile);
//       setFileName(selectedFile.name); // Set the selected file name
//     }
//   };

//   // Handle file upload to the backend
//   const handleFileUpload = async () => {
//     if (!file) {
//       alert("Please select a file to upload.");
//       return;
//     }

//     const formData = new FormData();
//     formData.append("file", file);

//     try {
//       setLoading(true); // Show loading bar
//       loadingRef.current.continuousStart(); // Start the loading bar

//       const response = await axios.post("http://localhost:8000/upload/", formData, {
//         headers: {
//           "Content-Type": "multipart/form-data",
//         },
//       });

//       alert(`File uploaded successfully: ${response.data.filename}`);
//     } catch (error) {
//       console.error("Error uploading file:", error);
//       alert("Failed to upload the file.");
//     } finally {
//       setLoading(false);  // Hide loading bar
//       loadingRef.current.complete(); // Complete the loading bar
//     }
//   };

//   // Handle query input change
//   const handleQueryChange = (event) => {
//     setQuery(event.target.value);
//   };

//   // Handle query submission to the backend
//   const handleQuerySubmit = async () => {
//     if (!query) {
//       alert("Please enter a query.");
//       return;
//     }

//     setUserMessage(query); // Display the user's query in the chat window

//     try {
//       setLoading(true); // Show loading bar
//       loadingRef.current.continuousStart(); // Start the loading bar

//       const response = await axios.post("http://localhost:8000/chatbot/", new URLSearchParams({ query }));
//       setAiMessage(response.data.answer); // Display AI's response
//       setQuery(""); // Clear the input field after sending the query
//     } catch (error) {
//       console.error("Error querying chatbot:", error);
//       setAiMessage("Failed to get a response from the AI.");
//     } finally {
//       setLoading(false);  // Hide loading bar
//       loadingRef.current.complete(); // Complete the loading bar
//     }
//   };

//   // Render the AI response with HTML tags (e.g., bold, numbered lists)
//   const renderAiMessage = () => {
//     if (!aiMessage) return null;
  
//     // Use marked to convert markdown to HTML
//     const htmlContent = marked(aiMessage);
  
//     return (
//       <div
//         className="message"
//         dangerouslySetInnerHTML={{
//           __html: htmlContent,  // Insert the parsed HTML content
//         }}
//       />
//     );
//   };
  

//   return (
//     <div className="App">
//       <LoadingBar color="#f11946" ref={loadingRef} />  {/* Loading bar */}
      
//       <aside className="sidemenu">
//         <div className="logo-section">
//           <img src="/factor_law_logo-removebg-preview.png" alt="Factor Law Logo" className="logo" />
//           <h1 className="company-name">Factor Law</h1>
//         </div>
//         <div className="side-menu-button">
//           <label htmlFor="file-upload" className="custom-file-upload">
//             <span>+ </span> Upload New File
//           </label>
//           <input
//             id="file-upload"
//             type="file"
//             style={{ display: 'none' }}
//             onChange={handleFileChange}
//           />
//           <button onClick={handleFileUpload} className="upload-button" disabled={loading}>
//             {loading ? "Uploading..." : "Upload File"}
//           </button>
//           {fileName && (
//             <p className="file-name-display">Selected File: {fileName}</p>
//           )}
//         </div>
//       </aside>
      
//       <section className="chatbox">
//         <div className="chat-log">
//           {userMessage && (
//             <div className="chat-message">
//               <div className="chat-message-center">
//                 <div className="avatar"></div>
//                 <div className="message">{userMessage}</div>
//               </div>
//             </div>
//           )}

//           {aiMessage && (
//             <div className="chat-message-ai">
//               <div className="chat-message-center">
//                 <div className="avatar_ai">
//                   <Logo />
//                 </div>
//                 {renderAiMessage()}
//               </div>
//             </div>
//           )}
//         </div>

//         <div className="chat-input-holder">
//           <textarea
//             rows="1"
//             className="chat-input-textarea"
//             placeholder="Ask anything about the contract"
//             value={query}
//             onChange={handleQueryChange}
//             disabled={loading}
//           ></textarea>
//           <button className="send-button" onClick={handleQuerySubmit} disabled={loading}>
//             {loading ? "Processing..." : "Send"}
//           </button>
//         </div>
//       </section>
//     </div>
//   );
// }

// export default App;