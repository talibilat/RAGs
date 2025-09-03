import React from 'react';  // Import React

// Define the Logo component using an SVG element
const Logo = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"  // Define the XML namespace for SVG
    width="40"  // Set the width of the SVG
    height="40"  // Set the height of the SVG
    viewBox="0 0 200 200"  // Define the viewbox dimensions of the SVG
  >
    {/* Red background circle */}
    <circle cx="100" cy="100" r="100" fill="#C4161C" />

    {/* White dots inside the red circle */}
    <circle cx="70" cy="60" r="12" fill="#ffffff" />
    <circle cx="100" cy="60" r="12" fill="#ffffff" />
    <circle cx="130" cy="60" r="12" fill="#ffffff" />
    <circle cx="70" cy="100" r="12" fill="#ffffff" />
    <circle cx="100" cy="100" r="12" fill="#ffffff" />
    <circle cx="70" cy="140" r="12" fill="#ffffff" />
  </svg>
);

export default Logo;  // Export the Logo component for use in other parts of the application
