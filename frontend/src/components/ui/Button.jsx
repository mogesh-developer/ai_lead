import React from 'react';

const Button = ({ children, variant = 'primary', size = 'md', className = '', ...props }) => {
  const base = 'inline-flex items-center justify-center font-semibold rounded transition-all focus:outline-none';
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-3 text-base'
  };
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50',
    success: 'bg-green-600 text-white hover:bg-green-700',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  };

  return (
    <button className={`${base} ${sizes[size]} ${variants[variant] || variants.primary} ${className}`} {...props}>
      {children}
    </button>
  );
};

export default Button;
