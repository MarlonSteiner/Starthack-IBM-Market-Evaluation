import React from 'react';

const DraftingArea = ({ articles, draftingArticleIds, onSendForReview }) => {
    
    const compiledText = articles
        .filter(article => draftingArticleIds.includes(article.id))
        .map(article => article.draftText)
        .join('\n\n---\n\n');

    // KORREKTUR: 'mt-8' (margin-top) entfernt.
    // Der Abstand wird jetzt zentral in App.jsx durch 'gap-8' gesteuert.
    return (
        <div className="bg-white p-6 border border-gray-200 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Compiled Draft Text</h3>
            
            <textarea
                readOnly
                value={compiledText}
                placeholder="Click 'Add to Draft Text' on a news article to collect its content here..."
                className="w-full h-64 p-3 bg-slate-50 border border-gray-200 rounded-md text-gray-800 text-sm leading-relaxed font-mono focus:outline-none"
            />

            <button
                onClick={onSendForReview}
                disabled={!compiledText}
                className="w-full mt-4 px-4 py-2 text-sm font-medium text-white bg-slate-700 border border-slate-700 rounded-md hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 disabled:bg-slate-400 disabled:cursor-not-allowed"
            >
                Send for human review
            </button>
        </div>
    );
};

export default DraftingArea;