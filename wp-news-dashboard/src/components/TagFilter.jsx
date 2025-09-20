import React, { useState } from 'react';

const TagFilter = ({ allTags, selectedTags, onTagToggle, onAddNewTag, onClearFilters }) => {
    const [newTagInput, setNewTagInput] = useState('');

    const handleAddTag = (e) => {
        e.preventDefault();
        if (newTagInput && !allTags.find(t => t.name.toLowerCase() === newTagInput.toLowerCase())) {
            onAddNewTag(newTagInput);
            setNewTagInput('');
        }
    };

    // KORREKTUR: Alle alten Layout-Klassen entfernt. 
    // Die Komponente ist jetzt ein einfacher Container.
    return (
        <div className="bg-white p-6 border border-gray-200 rounded-lg">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Filter by Tags</h3>
                {selectedTags.length > 0 && (
                     <button 
                        onClick={onClearFilters}
                        className="text-sm text-slate-600 hover:text-slate-900 font-medium">
                        Clear
                    </button>
                )}
            </div>

            <div className="flex flex-wrap gap-2 mb-6">
                {allTags.map(tag => {
                    const isSelected = selectedTags.includes(tag.name);
                    return (
                        <button
                            key={tag.id}
                            onClick={() => onTagToggle(tag.name)}
                            className={`px-3 py-1 text-sm font-medium rounded-full border transition-colors duration-200 ${
                                isSelected 
                                ? 'bg-slate-700 text-white border-slate-700' 
                                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'
                            }`}
                        >
                            {tag.name}
                        </button>
                    );
                })}
            </div>

            <form onSubmit={handleAddTag}>
                <label htmlFor="new-tag" className="block text-sm font-medium text-gray-700 mb-1">
                    Add New Tag
                </label>
                <div className="flex items-center space-x-2">
                    <input
                        type="text"
                        id="new-tag"
                        value={newTagInput}
                        onChange={(e) => setNewTagInput(e.target.value)}
                        placeholder="e.g., Inflation"
                        className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-slate-500 focus:border-slate-500 sm:text-sm"
                    />
                    <button 
                        type="submit"
                        className="px-4 py-2 text-sm font-medium text-white bg-slate-700 border border-slate-700 rounded-md hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500"
                    >
                        Add
                    </button>
                </div>
            </form>
        </div>
    );
};

export default TagFilter;