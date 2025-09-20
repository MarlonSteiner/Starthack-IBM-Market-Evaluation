import React from 'react';
import { CheckCircleIcon, XCircleIcon, ExternalLinkIcon } from './icons';

// Das Farb-Mapping bleibt bestehen
const priorityColors = {
    High: 'bg-red-500',
    Medium: 'bg-yellow-400',
    Low: 'bg-green-500',
};

const NewsArticleCard = ({ article, onToggleDraft, isDrafting }) => {
    
    const cardStyle = isDrafting ? 'border-slate-500 shadow-md' : 'border-gray-200';
    const buttonStyle = isDrafting 
        ? 'bg-red-600 hover:bg-red-700 text-white'
        : 'bg-slate-700 hover:bg-slate-800 text-white';

    return (
        <div className={`relative rounded-lg border overflow-hidden mb-6 transition-all duration-300 bg-white ${cardStyle}`}>
            
            {/* AKTUALISIERTER PRIORITÄTS-INDIKATOR MIT TEXT */}
            <div 
                className={`absolute top-4 right-4 px-2.5 py-1 text-xs font-semibold text-white rounded-full ${priorityColors[article.priority] || 'bg-gray-300'}`}
            >
                Priority: {article.priority} 
            </div>

            <div className="p-6">
                <div className="mb-3">
                    {/* Metadaten bleiben auf 'font-medium' (geerbt) */}
                    <p className="text-sm text-slate-500">{article.source} &middot; {article.date}</p>
                    {/* Titel bleibt auf 'font-semibold', um hervorzustechen */}
                    <h2 className="text-xl font-semibold text-slate-800 mt-1 pr-28">{article.title}</h2>
                    <div className="flex flex-wrap gap-2 mt-3">
                        {/* Tags bleiben 'font-semibold' für gute Lesbarkeit */}
                        {article.tags.map(tag => (
                            <span key={tag} className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-slate-700">
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>
                {/* Zwischenüberschriften bleiben auf 'font-medium' (geerbt) */}
                <p className="text-sm text-slate-500 uppercase tracking-wider">Summary</p>
                {/* Fließtext erbt 'font-medium' */}
                <p className="mt-2 p-2 bordertext-slate-700 leading-relaxed">{article.summary}</p>
                <p className="mt-1 p-1 text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Why it matters</p>
                <div className="mt-2 p-4 bg-gray-100 border border-slate-200 rounded-md">
                    <p className="text-gray-700 leading-relaxed">{article.context}</p>
                </div>
                <div className="mt-4">
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Draft Text for Human Review</p>
                    <div className="bg-gray-100 p-4 border border-gray-200 rounded-md text-gray-800 leading-relaxed whitespace-pre-wrap">
                        {article.draftText}
                    </div>
                </div>
            </div>

            <div className="bg-gray-100 px-6 py-3 flex justify-between items-center border-t">
                <a href={article.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-200 transition-colors">
                    <ExternalLinkIcon className="w-4 h-4" />
                    <span>View Source</span>
                </a>
                <button onClick={() => onToggleDraft(article.id)}
                    className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${buttonStyle}`}>
                    {isDrafting ? <XCircleIcon className="w-4 h-4" /> : <CheckCircleIcon className="w-4 h-4" />}
                    <span>{isDrafting ? 'Remove from Draft' : 'Add to Draft Text'}</span>
                </button>
            </div>
        </div>
    );
};

export default NewsArticleCard;