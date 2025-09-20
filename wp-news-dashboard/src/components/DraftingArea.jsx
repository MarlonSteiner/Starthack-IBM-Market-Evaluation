import React from 'react';

const DraftingArea = ({ articles, draftingArticleIds, onSendForReview }) => {
    
    const compiledText = articles
        .filter(article => draftingArticleIds.includes(article.id))
        .map(article => article.draftText)
        .join('\n\n---\n\n');

    return (
        // HINZUGEFÜGT: shadow-sm für einen dezenten Schatten
        <div className="bg-white p-6 border border-slate-200 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Compiled Draft Text</h3>
            <textarea
                readOnly
                value={compiledText}
                placeholder="Click 'Add to Draft Text' on a news article to collect its content here..."
                className="w-full h-64 p-3 bg-slate-100 border border-slate-200 rounded-md text-slate-800 text-sm leading-relaxed font-mono focus:outline-none"
            />
            <button
                onClick={onSendForReview}
                disabled={!compiledText}
                className="w-full mt-4 px-4 py-2 text-sm text-white bg-slate-700 border border-slate-700 rounded-md hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 disabled:bg-slate-400 disabled:cursor-not-allowed"
            >
                Send for human review
            </button>
        </div>
    );
};

export default DraftingArea;