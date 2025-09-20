import React from 'react';

const DraftingArea = ({ articles, draftingArticleIds, onSendForReview }) => {
    
    // Zuerst die ausgewählten Artikel filtern
    const draftedArticles = articles
        .filter(article => draftingArticleIds.includes(article.id));

    // Dann den Text und die Quellen aus den gefilterten Artikeln extrahieren
    const compiledText = draftedArticles
        .map(article => article.draftText)
        .join('\n\n---\n\n');

    // Extrahiert die Quellen und stellt sicher, dass jede nur einmal vorkommt
    const uniqueSources = [...new Set(draftedArticles.map(article => article.source))];

    return (
        <div className="bg-white p-6 border border-slate-200 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Compiled Draft Text</h3>
            <textarea
                readOnly
                value={compiledText}
                placeholder="Click 'Add to Draft Text' on a news article to collect its content here..."
                className="w-full h-64 p-3 bg-slate-100 border border-slate-200 rounded-md text-slate-800 text-sm leading-relaxed focus:outline-none"
            />

            {/* NEUER BEREICH FÜR DIE QUELLEN */}
            {/* Wird nur angezeigt, wenn mindestens eine Quelle vorhanden ist */}
            {uniqueSources.length > 0 && (
                <div className="mt-4">
                    <h4 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-2">Sources</h4>
                    <div className="flex flex-wrap gap-2">
                        {uniqueSources.map(source => (
                            <span 
                                key={source} 
                                className="px-2.5 py-1 text-xs font-semibold rounded-md bg-slate-100 text-slate-700"
                            >
                                {source}
                            </span>
                        ))}
                    </div>
                </div>
            )}

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