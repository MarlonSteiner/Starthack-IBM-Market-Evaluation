import React, { useState } from 'react';

const TagFilter = ({ allTags, selectedTags, onTagToggle, onAddNewTag, onClearFilters, tagMessage }) => {
    const [newTagInput, setNewTagInput] = useState('');

    const handleAddTag = (e) => {
        e.preventDefault();
        if (newTagInput) {
            onAddNewTag(newTagInput);
            setNewTagInput('');
        }
    };

    return (
        <div className="bg-white p-6 border border-slate-200 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Nach Tags filtern</h3>
                {selectedTags.length > 0 && (
                    <button 
                        onClick={onClearFilters}
                        className="text-sm text-slate-600 hover:text-slate-900 font-medium">
                        Zurücksetzen
                    </button>
                )}
            </div>
            <div className="flex flex-wrap gap-2 mb-6">
                {allTags.map(tag => {
                    const isSelected = selectedTags.includes(tag.name);
                    return (
                        <button key={tag.id} onClick={() => onTagToggle(tag.name)}
                            className={`px-3 py-1 text-sm font-medium rounded-full border transition-colors duration-200 ${
                                isSelected 
                                ? 'bg-slate-700 text-white border-slate-700' 
                                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                            }`}
                        >
                            {tag.name}
                        </button>
                    );
                })}
            </div>
            <form onSubmit={handleAddTag}>
                <label htmlFor="new-tag" className="block text-sm font-medium text-slate-700 mb-1">
                    Neuen Tag hinzufügen
                </label>
                <div className="flex items-center space-x-2">
                    <input type="text" id="new-tag" value={newTagInput} onChange={(e) => setNewTagInput(e.target.value)}
                        placeholder="z.B. Inflation"
                        className="block w-full px-3 py-2 bg-white border border-slate-300 rounded-md placeholder-slate-400 focus:outline-none focus:ring-slate-500 focus:border-slate-500 sm:text-sm"
                    />
                    <button type="submit"
                        className="px-4 py-2 text-sm font-medium text-white bg-slate-700 border border-slate-700 rounded-md hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500"
                    >
                        Hinzufügen
                    </button>
                </div>
            </form>
            <div className="h-6 mt-2">
                {tagMessage && (
                    <p className="text-red-600 text-sm text-center animate-pulse">
                        {tagMessage}
                    </p>
                )}
            </div>
        </div>
    );
};

export default TagFilter;