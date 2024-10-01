import React from 'react';  // Import React

// Define a functional component to display the user image
const UserImage = () => {
  return (
    <img 
      // Reference the image from the public folder using process.env.PUBLIC_URL
      src={`${process.env.PUBLIC_URL}/1718214568589.jpeg`}  
      
      // Provide alt text for accessibility
      alt="User Avatar"  
      
      // Apply inline styles to make the image circular and set its size
      style={{ 
        width: "40px",       // Set the width of the image
        height: "40px",      // Set the height of the image
        borderRadius: "50%"  // Make the image circular
      }}  
    />
  );
};

// Export the component to be used in other parts of the application
export default UserImage;
