import React from 'react';

const TimeFilter = ({ hours, onHoursChange }) => {
  return (
    <div className="bg-white p-6 border border-slate-200 rounded-lg shadow-md">
      <h3 className="text-lg font-semibold text-slate-800 mb-4">Filter by Time</h3>
      <div className="space-y-4">
        <input
          type="range"
          min="0"
          max="72"
          value={hours}
          onChange={(e) => onHoursChange(parseInt(e.target.value, 10))}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
        />
        <div className="text-center text-sm text-slate-600 font-medium">
          Show news from the last <span className="font-bold text-slate-800">{hours}</span> hours
        </div>
      </div>
    </div>
  );
};

export default TimeFilter;