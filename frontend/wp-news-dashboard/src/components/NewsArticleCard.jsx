import React from 'react';
import { CheckCircleIcon, XCircleIcon, ExternalLinkIcon } from './icons';

const priorityColors = {
    High: 'bg-red-500',
    Medium: 'bg-yellow-400', 
    Low: 'bg-green-500',
};

// Übesetzung für die Anzeige der Priorität
const priorityLabels = {
    High: 'Hoch',
    Medium: 'Mittel',
    Low: 'Niedrig',
};

const NewsArticleCard = ({ article, onToggleDraft, isDrafting }) => {
    
    const cardStyle = isDrafting 
        ? 'border-slate-500 shadow-md' 
        : 'border-slate-200 shadow-md';
    
    const buttonStyle = isDrafting 
        ? 'bg-red-600 hover:bg-red-700 text-white'
        : 'bg-slate-700 hover:bg-slate-800 text-white';

    const displayDate = article.datetime ? article.datetime.split('T')[0] : '';

    return (
        <div className={`relative rounded-lg border overflow-hidden mb-6 transition-all duration-300 bg-white ${cardStyle}`}>
            
            <div className={`absolute top-4 right-4 px-2.5 py-1 text-xs font-semibold text-white rounded-full ${priorityColors[article.priority] || 'bg-slate-300'}`}>
                Priorität: {priorityLabels[article.priority] || article.priority} 
            </div>

            <div className="p-6">
                <div className="mb-3">
                    <p className="text-sm text-slate-500">{article.source} &middot; {displayDate}</p>
                    <h2 className="text-xl font-semibold text-slate-800 mt-1 pr-28">{article.title}</h2>
                    <div className="flex flex-wrap gap-2 mt-3">
                        {article.tags.map(tag => (
                            <span key={tag} className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-slate-700">
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>
                <p className="text-sm text-slate-500 uppercase tracking-wider mt-4 mb-2">Zusammenfassung</p>
                <p className="text-slate-700 text-sm leading-relaxed">{article.summary}</p>
                
                <p className="mt-4 text-sm text-slate-500 uppercase tracking-wider mb-2">Relevanz</p>
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-md">
                    <p className="text-slate-700 text-sm leading-relaxed">{article.context}</p>
                </div>
                <div className="mt-4">
                    <p className="text-sm text-slate-500 uppercase tracking-wider mb-2">Textentwurf zur Überprüfung</p>
                    <div className="bg-slate-100 p-4 border border-slate-200 rounded-md text-slate-800 text-sm leading-relaxed whitespace-pre-wrap">
                        {article.draftText}
                    </div>
                </div>
            </div>

            <div className="bg-slate-50 px-6 py-3 flex justify-between items-center border-t border-slate-200">
                <a href={article.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-100 transition-colors">
                    <ExternalLinkIcon className="w-4 h-4" />
                    <span>Quelle ansehen</span>
                </a>
                <button onClick={() => onToggleDraft(article.id)}
                    className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${buttonStyle}`}>
                    {isDrafting ? <XCircleIcon className="w-4 h-4" /> : <CheckCircleIcon className="w-4 h-4" />}
                    <span>{isDrafting ? 'Vom Entwurf entfernen' : 'Zum Entwurf hinzufügen'}</span>
                </button>
            </div>
        </div>
    );
};

export default NewsArticleCard;