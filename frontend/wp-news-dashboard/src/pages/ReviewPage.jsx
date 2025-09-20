import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ExternalLinkIcon } from '../components/icons';

const ReviewPage = ({ items, onApprove, onReject }) => {
    const [editedItems, setEditedItems] = useState({});

    const handleTextChange = (id, newText) => {
        setEditedItems(prev => ({ ...prev, [id]: newText }));
    };

    const handleApproveClick = (item) => {
        const finalText = editedItems[item.id] ?? item.text;
        onApprove(item.id, finalText);
    };

    return (
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Link to="/" className="text-slate-600 hover:text-slate-900 font-medium mb-6 inline-block">
                &larr; Zurück zur Startseite
            </Link>
            
            <h1 className="text-3xl font-bold text-slate-800 mb-8">Zu überprüfende Texte</h1>

            {items.length === 0 ? (
                <p className="text-slate-500 text-center py-16">Keine Einträge zur Überprüfung vorhanden.</p>
            ) : (
                <div className="space-y-8">
                    {items.map(item => (
                        <div key={item.id} className="bg-white p-4 border border-slate-200 rounded-lg shadow-md flex items-start gap-6">
                            
                            {/* WICHTIG: Dieser Block zeigt die Quellen an */}
                            <div className="w-1/4 flex-shrink-0">
                                <h4 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-3">Quellen</h4>
                                <ul className="space-y-2">
                                    {item.sources && item.sources.map(source => (
                                        <li key={source.name}>
                                            <a
                                                href={source.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="flex items-center text-sm text-slate-700 hover:text-slate-900 hover:underline"
                                            >
                                                <ExternalLinkIcon className="w-4 h-4 mr-2 flex-shrink-0" />
                                                <span>{source.name}</span>
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            
                            <div className="flex-grow flex items-start gap-4">
                                <textarea
                                    value={editedItems[item.id] ?? item.text}
                                    onChange={(e) => handleTextChange(item.id, e.target.value)}
                                    className="w-full h-48 p-3 bg-slate-50 border border-slate-200 rounded-md text-slate-800 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-slate-500"
                                />
                                <div className="flex flex-col gap-2">
                                    <button
                                        onClick={() => handleApproveClick(item)}
                                        className="p-3 bg-green-100 text-green-700 hover:bg-green-200 rounded-md transition-colors"
                                        aria-label="Akzeptieren"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                    </button>
                                    <button
                                        onClick={() => onReject(item.id)}
                                        className="p-3 bg-red-100 text-red-700 hover:bg-red-200 rounded-md transition-colors"
                                        aria-label="Ablehnen"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ReviewPage;