import React from 'react';

const Card = ({ children, className = '', header = null }) => {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden ${className}`}>
      {header && (
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
          {header}
        </div>
      )}
      <div className="p-6">
        {children}
      </div>
    </div>
  );
};

export default Card;