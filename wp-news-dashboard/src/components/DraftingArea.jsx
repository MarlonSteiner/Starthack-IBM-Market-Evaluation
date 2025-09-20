import React from 'react';

const DraftingArea = ({ articles, draftingArticleIds, onSendForReview }) => {
    
    const draftedArticles = articles
        .filter(article => draftingArticleIds.includes(article.id));

    const compiledText = draftedArticles
        .map(article => article.draftText)
        .join('\n\n---\n\n');

    // Stellt sicher, dass wir einzigartige Quell-Objekte (Name und URL) sammeln
    const uniqueSourceObjects = Array.from(
        new Map(draftedArticles.map(article => 
            [article.source, { name: article.source, url: article.url }]
        )).values()
    );

    const handleSendClick = () => {
        if (compiledText) {
            // WICHTIG: Stellt sicher, dass 'sources' hier übergeben wird
            onSendForReview(compiledText, uniqueSourceObjects);
        }
    };

    return (
        <div className="bg-white p-6 border border-slate-200 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Zusammengestellter Entwurf</h3>
            <textarea
                readOnly
                value={compiledText}
                placeholder="Klicke bei einem Artikel auf 'Zum Entwurf hinzufügen', um den Inhalt hier zu sammeln..."
                className="w-full h-64 p-3 bg-slate-100 border border-slate-200 rounded-md text-slate-800 text-sm leading-relaxed focus:outline-none"
            />
            {uniqueSourceObjects.length > 0 && (
                <div className="mt-4">
                    <h4 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-2">Quellen</h4>
                    <div className="flex flex-wrap gap-2">
                        {uniqueSourceObjects.map(source => (
                            <span 
                                key={source.name} 
                                className="px-2.5 py-1 text-xs font-semibold rounded-md bg-slate-100 text-slate-700"
                            >
                                {source.name}
                            </span>
                        ))}
                    </div>
                </div>
            )}
            <button
                onClick={handleSendClick}
                disabled={!compiledText}
                className="w-full mt-4 px-4 py-2 text-sm font-medium text-white bg-slate-700 border border-slate-700 rounded-md hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 disabled:bg-slate-400 disabled:cursor-not-allowed"
            >
                Zur Überprüfung senden
            </button>
        </div>
    );
};

export default DraftingArea;