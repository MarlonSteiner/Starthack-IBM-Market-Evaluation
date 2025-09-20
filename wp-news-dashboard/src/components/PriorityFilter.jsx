import React from 'react';

// Wir trennen die internen Datenwerte von den angezeigten Labels
const priorities = [
    { value: 'High', label: 'Hoch' },
    { value: 'Medium', label: 'Mittel' },
    { value: 'Low', label: 'Niedrig' }
];

const PriorityFilter = ({ selectedPriorities, onPriorityToggle }) => {
    return (
        <div className="bg-white p-6 border border-slate-200 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Nach Priorität filtern</h3>
            <div className="flex flex-wrap gap-2">
                {priorities.map(priority => {
                    const isSelected = selectedPriorities.includes(priority.value);
                    return (
                        <button
                            key={priority.value}
                            onClick={() => onPriorityToggle(priority.value)}
                            className={`px-3 py-1 text-sm font-medium rounded-full border transition-colors duration-200 ${
                                isSelected 
                                ? 'bg-slate-700 text-white border-slate-700' 
                                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                            }`}
                        >
                            {priority.label}
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default PriorityFilter;