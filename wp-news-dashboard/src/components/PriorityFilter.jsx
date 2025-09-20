import React from 'react';

const priorities = ['High', 'Medium', 'Low'];

const PriorityFilter = ({ selectedPriorities, onPriorityToggle }) => {
    return (
        <div className="bg-white p-6 border border-gray-200 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Filter by Priority</h3>
            <div className="flex flex-wrap gap-2">
                {priorities.map(priority => {
                    const isSelected = selectedPriorities.includes(priority);
                    return (
                        <button
                            key={priority}
                            onClick={() => onPriorityToggle(priority)}
                            className={`px-3 py-1 text-sm font-medium rounded-full border transition-colors duration-200 ${
                                isSelected 
                                ? 'bg-slate-700 text-white border-slate-700' 
                                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'
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