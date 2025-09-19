import React from 'react';

const Sidebar = () => (
    <aside className="w-full lg:w-1/4 lg:pl-8 mt-8 lg:mt-0">
        <div className="sticky top-8">
             <div className="bg-white p-6 border border-gray-200 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">News</h3>
                <ul>
                    <li className="border-b border-gray-200 py-3">
                        <p className="text-sm text-gray-600 font-medium">Neuer Podcast ist live! // Seit 1. September</p>
                        <p className="text-xs text-gray-400 mt-1">1. September 2025</p>
                    </li>
                    <li className="border-b border-gray-200 py-3">
                        <p className="text-sm text-gray-600 font-medium">Neuer Podcast ab 1. September 2025 // Mit dem Podcast «WP Weekly Perspectives»</p>
                        <p className="text-xs text-gray-400 mt-1">21. August 2025</p>
                    </li>
                     <li className="py-3">
                        <p className="text-sm text-gray-600 font-medium">W&P is hiring a new research analyst.</p>
                        <p className="text-xs text-gray-400 mt-1">15. August 2025</p>
                    </li>
                </ul>
            </div>
        </div>
    </aside>
);

export default Sidebar;