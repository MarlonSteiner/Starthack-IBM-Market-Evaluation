import React from 'react';
// Das neue Icon importieren
import { CheckCircleIcon, XCircleIcon, ExternalLinkIcon } from './icons';

const NewsArticleCard = ({ article, onToggleDraft, isDrafting }) => {
    
    const cardStyle = isDrafting ? 'border-slate-500 shadow-md' : 'border-gray-200';
    const buttonStyle = isDrafting 
        ? 'bg-red-600 hover:bg-red-700 text-white'
        : 'bg-slate-700 hover:bg-slate-800 text-white';

    return (
        <div className={`rounded-lg border overflow-hidden mb-6 transition-all duration-300 bg-white ${cardStyle}`}>
            <div className="p-6">
                {/* ... (Der obere Teil der Karte bleibt unverändert) ... */}
                <div className="mb-3">
                    <p className="text-sm text-gray-500">{article.source} &middot; {article.date}</p>
                    <h2 className="text-xl font-semibold text-gray-800 mt-1">{article.title}</h2>
                    <div className="flex flex-wrap gap-2 mt-3">
                        {article.tags.map(tag => (
                            <span key={tag} className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2 mt-4">Summary</p>
                <p className="text-gray-700 leading-relaxed">{article.summary}</p>
                <div className="mt-4 p-4 bg-slate-100 border border-slate-200 rounded-md">
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Why it matters</p>
                    <p className="text-gray-700 leading-relaxed">{article.context}</p>
                </div>
                <div className="mt-4">
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Draft Text for Human Review</p>
                    <div className="bg-gray-100 p-4 border border-gray-200 rounded-md text-gray-800 text-sm leading-relaxed whitespace-pre-wrap font-mono">
                        {article.draftText}
                    </div>
                </div>
            </div>

            {/* AKTUALISIERTE AKTIONSLEISTE */}
            <div className="bg-gray-100 px-6 py-3 flex justify-between items-center border-t">
                {/* NEUER LINK-BUTTON LINKS */}
                <a
                    href={article.url}
                    target="_blank" // Öffnet den Link in einem neuen Tab
                    rel="noopener noreferrer" // Wichtig für die Sicherheit
                    className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-200 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500"
                >
                    <ExternalLinkIcon className="w-4 h-4" />
                    <span>View Source</span>
                </a>
                
                {/* Bestehender Button RECHTS */}
                <button 
                    onClick={() => onToggleDraft(article.id)}
                    className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 ${buttonStyle}`}
                >
                    {isDrafting ? <XCircleIcon className="w-4 h-4" /> : <CheckCircleIcon className="w-4 h-4" />}
                    <span>{isDrafting ? 'Remove from Draft' : 'Add to Draft Text'}</span>
                </button>
            </div>
        </div>
    );
};

export default NewsArticleCard;