import React, { useState, useEffect } from 'react';

// Import data
import { mockNewsData } from './data/mockNewsData';

// Import components
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import NewsArticleCard from './components/NewsArticleCard';

function App() {
    // In the future, this state will be populated by a backend API call
    const [articles, setArticles] = useState([]);

    // Simulate fetching data when the component mounts
    useEffect(() => {
        // Replace this with your API fetch logic
        setArticles(mockNewsData);
    }, []);

    return (
        <div className="bg-gray-50 min-h-screen font-sans text-gray-900">
            <Header />
            
            <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="text-left mb-10">
                    <h1 className="text-3xl font-light text-gray-800">Wellershoff & Partners, eine unabhängige Wirtschaftsberatung.</h1>
                    <p className="mt-2 text-lg text-gray-600 max-w-3xl">This internal dashboard acts as an early-warning system to detect, summarize, and provide context on relevant news for our clients.</p>
                </div>

                <div className="flex flex-col lg:flex-row">
                    <div className="w-full lg:w-3/4">
                       {articles.map(article => (
                           <NewsArticleCard key={article.id} article={article} />
                       ))}
                    </div>
                    <Sidebar />
                </div>
                 <footer className="text-center mt-12 py-6 border-t border-gray-200">
                    <p className="text-sm text-gray-500">© 2025 Wellershoff & Partners. All rights reserved.</p>
                </footer>
            </main>
        </div>
    );
}

export default App;