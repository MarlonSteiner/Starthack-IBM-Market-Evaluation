import React from 'react';
import RelevanceBadge from './RelevanceBadge';
import { CheckCircleIcon, EditIcon, XCircleIcon } from './icons';

const NewsArticleCard = ({ article }) => (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6 transition-shadow hover:shadow-lg">
        <div className="p-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-3">
                <div className="mb-2 sm:mb-0">
                    <p className="text-sm text-gray-500">{article.source} &middot; {article.date}</p>
                    <h2 className="text-xl font-semibold text-gray-800 mt-1">{article.title}</h2>
                </div>
                <div className="flex-shrink-0">
                    <RelevanceBadge relevance={article.relevance} />
                </div>
            </div>
            
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2 mt-4">Summary</p>
            <p className="text-gray-700 leading-relaxed">{article.summary}</p>
            
            <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-md">
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Why it matters</p>
                <p className="text-gray-700 leading-relaxed">{article.context}</p>
            </div>

            <div className="mt-4">
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Draft Text for Human Review</p>
                <div className="bg-gray-50 p-4 border border-gray-200 rounded-md text-gray-800 text-sm leading-relaxed whitespace-pre-wrap font-mono">
                    {article.draftText}
                </div>
            </div>
        </div>
        <div className="bg-gray-50 px-6 py-3 flex justify-end items-center space-x-3 border-t border-gray-200">
             <button className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500">
                <EditIcon className="w-4 h-4" />
                <span>Edit</span>
            </button>
            <button className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500">
                <XCircleIcon className="w-4 h-4" />
                <span>Dismiss</span>
            </button>
            <button className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-slate-700 border border-slate-700 rounded-md hover:bg-slate-800 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500">
                <CheckCircleIcon className="w-4 h-4" />
                <span>Approve & Distribute</span>
            </button>
        </div>
    </div>
);

export default NewsArticleCard;