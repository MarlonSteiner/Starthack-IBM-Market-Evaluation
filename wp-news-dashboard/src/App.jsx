import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';

// Komponenten importieren
import Header from './components/Header';
import TagFilter from './components/TagFilter';
import DraftingArea from './components/DraftingArea';
import NewsArticleCard from './components/NewsArticleCard';

const API_BASE_URL = 'http://localhost:3001/api';

function App() {
    const [articles, setArticles] = useState([]);
    const [allTags, setAllTags] = useState([]);
    const [selectedTags, setSelectedTags] = useState([]);
    const [draftingArticleIds, setDraftingArticleIds] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [articlesResponse, tagsResponse] = await Promise.all([
                    axios.get(`${API_BASE_URL}/articles`),
                    axios.get(`${API_BASE_URL}/tags`)
                ]);
                setArticles(articlesResponse.data);
                setAllTags(tagsResponse.data);
            } catch (err) {
                setError('Failed to load data from the server.');
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);
    
    const handleTagToggle = (tagName) => {
        setSelectedTags(prevTags => 
            prevTags.includes(tagName) 
            ? prevTags.filter(t => t !== tagName) 
            : [...prevTags, tagName]
        );
    };

    const handleAddNewTag = async (tagName) => {
        try {
            const response = await axios.post(`${API_BASE_URL}/tags`, { name: tagName });
            setAllTags(prev => [...prev, response.data]);
            handleTagToggle(tagName);
        } catch(err) {
            console.error("Failed to add new tag", err);
        }
    };
    
    const handleClearFilters = () => setSelectedTags([]);

    const filteredArticles = useMemo(() => {
        if (selectedTags.length === 0) return articles;
        return articles.filter(article => 
            article.tags.some(tag => selectedTags.includes(tag))
        );
    }, [articles, selectedTags]);

    const handleToggleDraft = (articleId) => {
        setDraftingArticleIds(prevIds => 
            prevIds.includes(articleId)
                ? prevIds.filter(id => id !== articleId)
                : [...prevIds, articleId]
        );
    };

    const handleSendForReview = () => {
        setDraftingArticleIds([]);
    };

    return (
        <div className="bg-gray-50 min-h-screen font-sans text-gray-900">
            <Header />
            <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="text-left mb-10">
                    <h1 className="text-3xl font-light text-gray-800">Wellershoff & Partners, eine unabhängige Wirtschaftsberatung.</h1>
                    <p className="mt-2 text-lg text-gray-600 max-w-3xl">This internal dashboard acts as an early-warning system to detect, summarize, and provide context on relevant news for our clients.</p>
                </div>
                
                {/* STABILES ZWEISPALTIGES GRID LAYOUT */}
                <div className="lg:grid lg:grid-cols-12 lg:gap-8">
                    
                    {/* LINKE SPALTE (Nachrichten) */}
                    <div className="lg:col-span-8">
                       {isLoading && <p>Loading articles...</p>}
                       {error && <p className="text-red-500">{error}</p>}
                       {!isLoading && !error && filteredArticles.map(article => (
                           <NewsArticleCard 
                                key={article.id} 
                                article={article} 
                                onToggleDraft={handleToggleDraft}
                                isDrafting={draftingArticleIds.includes(article.id)}
                            />
                       ))}
                       {!isLoading && filteredArticles.length === 0 && (
                           <div className="text-center py-10 bg-white border rounded-lg">
                               <h3 className="text-xl font-medium text-gray-700">No news articles found.</h3>
                               <p className="text-gray-500 mt-2">Try adjusting or clearing your tag filters.</p>
                           </div>
                       )}
                    </div>

                    {/* RECHTE SPALTE (Sidebar) */}
                    <div className="lg:col-span-4">
                         <div className="sticky top-8 flex flex-col gap-8">
                             <TagFilter 
                                allTags={allTags}
                                selectedTags={selectedTags}
                                onTagToggle={handleTagToggle}
                                onAddNewTag={handleAddNewTag}
                                onClearFilters={handleClearFilters}
                            />
                             <DraftingArea 
                                articles={articles}
                                draftingArticleIds={draftingArticleIds}
                                onSendForReview={handleSendForReview}
                             />
                         </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default App;