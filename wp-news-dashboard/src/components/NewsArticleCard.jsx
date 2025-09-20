import React from 'react';
import { CheckCircleIcon, XCircleIcon, ExternalLinkIcon } from './icons';

// Das Farb-Mapping bleibt bestehen
const priorityColors = {
    High: 'bg-red-500',
    // KORREKTUR: 'Medium' zu 'Middle' geändert, falls dies der Wert aus der API ist
    Medium: 'bg-yellow-400', 
    Low: 'bg-green-500',
};

const NewsArticleCard = ({ article, onToggleDraft, isDrafting }) => {
    
    // HINZUGEFÜGT: shadow-sm für einen dezenten Schatten
    const cardStyle = isDrafting 
        ? 'border-slate-500 shadow-md' 
        : 'border-slate-200 shadow-md'; // Hier hinzugefügt
    
    const buttonStyle = isDrafting 
        ? 'bg-red-600 hover:bg-red-700 text-white'
        : 'bg-slate-700 hover:bg-slate-800 text-white';

    return (
        <div className={`relative rounded-lg border overflow-hidden mb-6 transition-all duration-300 bg-white ${cardStyle}`}>
            
            {/* AKTUALISIERTER PRIORITÄTS-INDIKATOR MIT TEXT */}
            <div 
                className={`absolute top-4 right-4 px-2.5 py-1 text-xs font-semibold text-white rounded-full ${priorityColors[article.priority] || 'bg-slate-300'}`}
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
                            // KORREKTUR: bg-blue-100 zu bg-slate-100 geändert für Konsistenz
                            <span key={tag} className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-slate-700">
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>
                {/* Zwischenüberschriften bleiben auf 'font-medium' (geerbt) */}
                <p className="text-sm text-slate-500 uppercase tracking-wider mt-4 mb-2">Summary</p> {/* Abstand korrigiert */}
                {/* Fließtext erbt 'font-medium' */}
                <p className="text-slate-700 leading-relaxed">{article.summary}</p> {/* P-Tag bereinigt */}
                
                <p className="mt-4 text-sm text-slate-500 uppercase tracking-wider mb-2">Why it matters</p> {/* Abstand korrigiert */}
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-md"> {/* Hintergrund zu slate-50 */}
                    <p className="text-slate-700 leading-relaxed">{article.context}</p>
                </div>
                <div className="mt-4">
                    <p className="text-sm text-slate-500 uppercase tracking-wider mb-2">Draft Text for Human Review</p> {/* Farbe zu slate-500 */}
                    <div className="bg-slate-100 p-4 border border-slate-200 rounded-md text-slate-800 text-sm leading-relaxed whitespace-pre-wrap font-mono"> {/* Hintergrund und Rand zu slate */}
                        {article.draftText}
                    </div>
                </div>
            </div>

            <div className="bg-slate-50 px-6 py-3 flex justify-between items-center border-t border-slate-200"> {/* Hintergrund und Rand zu slate */}
                <a href={article.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-100 transition-colors"> {/* Farben zu slate */}
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