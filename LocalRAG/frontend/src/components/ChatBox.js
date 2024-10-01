import React, { useState } from 'react';
import axios from 'axios';
import { marked } from 'marked'; // Markdown parser for AI responses
import Logo from './Logo';  // AI logo component
import UserImage from './UserImage';  // User image component

const ChatBox = ({ userMessage, setUserMessage, aiMessage, setAiMessage, loading, setLoading, loadingRef }) => {
  const [query, setQuery] = useState("");  // State for user's query input

  const backendUrl = "http://localhost:8000";  // Backend URL for API requests

  // Handle input change for user query
  const handleQueryChange = (event) => {
    setQuery(event.target.value);
  };

  // Submit query to backend and handle response
  const handleQuerySubmit = async () => {
    if (!query) {
      alert("Please enter a query.");  // Alert if no query is entered
      return;
    }

    setUserMessage(query);  // Display the user's query in the chatbox

    try {
      setLoading(true);  // Set loading state
      loadingRef.current.continuousStart();  // Start the loading bar

      const response = await axios.post(`${backendUrl}/chatbot/`, new URLSearchParams({ query }));
      setAiMessage(response.data.answer);  // Set AI's response
      setQuery("");  // Clear the input field
    } catch (error) {
      console.error("Error querying chatbot:", error);  // Log error and update AI message with failure notice
      setAiMessage("Failed to get a response from the AI.");
    } finally {
      setLoading(false);  // Stop loading state
      loadingRef.current.complete();  // Complete the loading bar
    }
  };

  // Render AI message with markdown support
  const renderAiMessage = () => {
    if (!aiMessage) return null;  // If there's no AI message, return nothing
    const htmlContent = marked(aiMessage);  // Parse AI message markdown into HTML
    return <div className="message" dangerouslySetInnerHTML={{ __html: htmlContent }} />;  // Safely insert parsed HTML
  };

  return (
    <section className="chatbox">
      <div className="chat-log">
        {userMessage && (  // Conditionally render the user message if available
          <div className="chat-message">
            <div className="chat-message-center">
              <div className="avatar"> <UserImage /> </div>  {/* Display user avatar */}
              <div className="message">{userMessage}</div>  {/* Display user message */}
            </div>
          </div>
        )}

        {aiMessage && (  // Conditionally render the AI message if available
          <div className="chat-message-ai">
            <div className="chat-message-center">
              <div className="avatar_ai"> <Logo /> </div>  {/* Display AI logo */}
              {renderAiMessage()}  {/* Render AI's message */}
            </div>
          </div>
        )}
      </div>

      {/* Chat input and submit button */}
      <div className="chat-input-holder">
        <textarea
          rows="1"
          className="chat-input-textarea"
          placeholder="Ask anything about the contract"
          value={query}
          onChange={handleQueryChange}
          disabled={loading}  // Disable input if loading
        />
        <button className="send-button" onClick={handleQuerySubmit} disabled={loading}>
          {loading ? "Processing..." : "Send"}  {/* Display 'Send' or 'Processing...' based on loading state */}
        </button>
      </div>
    </section>
  );
};

export default ChatBox;
