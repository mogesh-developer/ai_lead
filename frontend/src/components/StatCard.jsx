import React from 'react';

const StatCard = ({ title, value, icon: Icon, color = 'blue', trend, trendValue }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600',
    red: 'bg-red-50 text-red-600',
    indigo: 'bg-indigo-50 text-indigo-600',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 transition-all hover:shadow-md">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color] || colorClasses.blue}`}>
          {Icon && <Icon className="w-6 h-6" />}
        </div>
        {trend && (
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${
            trend === 'up' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            {trend === 'up' ? '↑' : '↓'} {trendValue}%
          </span>
        )}
      </div>
      <div>
        <h3 className="text-sm font-medium text-gray-500">{title}</h3>
        <p className="text-2xl font-bold text-gray-900 mt-1">{value || 0}</p>
      </div>
    </div>
  );
};

export default StatCard;
