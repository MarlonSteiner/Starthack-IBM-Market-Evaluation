import React from 'react';

const priorities = ['High', 'Middle', 'Low'];

const PriorityFilter = ({ selectedPriorities, onPriorityToggle }) => {
    return (
        // HINZUGEFÜGT: shadow-sm für einen dezenten Schatten
        <div className="bg-white p-6 border border-slate-200 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Filter by Priority</h3>
            <div className="flex flex-wrap gap-2">
                {priorities.map(priority => {
                    const isSelected = selectedPriorities.includes(priority);
                    return (
                        <button
                            key={priority}
                            onClick={() => onPriorityToggle(priority)}
                            className={`px-3 py-1 text-sm rounded-full border transition-colors duration-200 ${
                                isSelected 
                                ? 'bg-slate-700 text-white border-slate-700' 
                                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                            }`}
                        >
                            {priority}
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default PriorityFilter;