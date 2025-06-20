// Placeholder Button component
import React from 'react';

export const Button = ({ children, className, ...props }) => {
  return (
    <button className={`px-4 py-2 rounded ${className}`} {...props}>
      {children}
    </button>
  );
};