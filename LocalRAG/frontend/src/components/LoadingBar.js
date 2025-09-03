import React, { forwardRef } from 'react';  // Import React and forwardRef from React
import LoadingBar from 'react-top-loading-bar';  // Import the LoadingBar component from the react-top-loading-bar package

// Define the TopLoadingBar component using forwardRef
// forwardRef allows the parent component to pass a ref to the child component (LoadingBar in this case)
const TopLoadingBar = forwardRef((props, ref) => {
  // Render the LoadingBar component, passing down the ref and allowing color customization via props
  // If no color prop is provided, it defaults to a red color (#f11946)
  return <LoadingBar color={props.color || "#f11946"} ref={ref} />;
});

export default TopLoadingBar;  // Export the TopLoadingBar component to be used in other parts of the app
