import React from 'react';

const StatCard = ({ title, value, icon = '📊', trend = '+0%', color = 'blue' }) => {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600 border-blue-400/20',
    purple: 'from-purple-500 to-purple-600 border-purple-400/20',
    yellow: 'from-yellow-500 to-yellow-600 border-yellow-400/20',
    green: 'from-emerald-500 to-emerald-600 border-emerald-400/20'
  };

  const textColorClasses = {
    blue: 'text-blue-400',
    purple: 'text-purple-400',
    yellow: 'text-yellow-400',
    green: 'text-emerald-400'
  };

  return (
    <div className={`bg-gradient-to-br from-slate-800 to-slate-700 rounded-lg p-6 border border-slate-600 hover:border-slate-500 transition-all duration-300 hover:shadow-lg hover:shadow-slate-900/50`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-slate-400 text-sm font-medium uppercase tracking-wider">{title}</p>
          <div className="flex items-baseline gap-2 mt-3">
            <p className="text-4xl font-bold text-white">{value}</p>
            <span className={`text-sm font-semibold ${textColorClasses[color]}`}>{trend}</span>
          </div>
        </div>
        <div className="text-4xl opacity-80">{icon}</div>
      </div>
      <div className="mt-4 h-1 bg-slate-600 rounded-full overflow-hidden">
        <div className={`h-full bg-gradient-to-r ${colorClasses[color]} rounded-full`} style={{ width: '70%' }}></div>
      </div>
    </div>
  );
};

export default StatCard;
