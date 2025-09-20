import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';

// Import all of your components
import Header from './components/Header';
import TagFilter from './components/TagFilter';
import PriorityFilter from './components/PriorityFilter';
import TimeFilter from './components/TimeFilter';
import SubscriptionBox from './components/SubscriptionBox';
import DraftingArea from './components/DraftingArea';
import NewsArticleCard from './components/NewsArticleCard';

const API_BASE_URL = 'http://localhost:3001/api';

function App() {
    // All state variables for the application
    const [articles, setArticles] = useState([]);
    const [allTags, setAllTags] = useState([]);
    const [selectedTags, setSelectedTags] = useState([]);
    const [selectedPriorities, setSelectedPriorities] = useState([]);
    const [draftingArticleIds, setDraftingArticleIds] = useState([]);
    const [timeFilterHours, setTimeFilterHours] = useState(72);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [tagMessage, setTagMessage] = useState('');

    // Effect to fetch initial data from the backend when the app loads
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [articlesResponse, tagsResponse] = await Promise.all([
                    axios.get(`${API_BASE_URL}/articles`),
                    axios.get(`${API_BASE_URL}/tags`)
                ]);
                const sortedArticles = articlesResponse.data.sort((a, b) => new Date(b.datetime) - new Date(a.datetime));
                setArticles(sortedArticles);
                setAllTags(tagsResponse.data);
            } catch (err) {
                setError('Daten konnten nicht vom Server geladen werden.');
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    // Handler for the new subscription box
    const handleSubscribe = async (email) => {
        try {
            const subscriptionData = {
                email,
                tags: selectedTags,
                priorities: selectedPriorities
            };
            await axios.post(`${API_BASE_URL}/subscribe`, subscriptionData);
        } catch (err) {
            console.error("Subscription failed:", err.response || err);
            alert("Fehler: Abonnement konnte nicht gespeichert werden.");
        }
    };

    // Handler for toggling priority filters
    const handlePriorityToggle = (priority) => {
        setSelectedPriorities(prev =>
            prev.includes(priority)
            ? prev.filter(p => p !== priority)
            : [...prev, priority]
        );
    };

    // Handler for the time filter slider
    const handleTimeFilterChange = (hours) => {
        setTimeFilterHours(hours);
    };

    // Handler for toggling tag filters
    const handleTagToggle = (tagName) => {
        setSelectedTags(prevTags =>
            prevTags.includes(tagName)
            ? prevTags.filter(t => t !== tagName)
            : [...prevTags, tagName]
        );
    };
    
    // Handler to clear all active filters
    const handleClearFilters = () => {
        setSelectedTags([]);
        setSelectedPriorities([]);
        setTimeFilterHours(72);
    };

    // Handler to add a new tag and process it on the backend
    const handleAddNewTag = async (tagName) => {
        setTagMessage('');
        try {
            const response = await axios.post(`${API_BASE_URL}/tags/process`, { name: tagName });
            const { updatedArticles, allTags: updatedAllTags } = response.data;
            setArticles(updatedArticles);
            setAllTags(updatedAllTags);
            setSelectedTags([tagName]); 
            
            const matches = updatedArticles.filter(article => 
                article.tags && article.tags.includes(tagName)
            );
            
            if (matches.length === 0) {
                setTagMessage('Keine Artikel für diesen Tag gefunden');
                setTimeout(() => {
                    setTagMessage('');
                }, 3000);
            }
        } catch (err) {
            console.error("API Call Failed:", err.response || err);
            alert("Fehler: Neuer Tag konnte nicht verarbeitet werden. Details in der Konsole.");
        }
    };

    // Handler to add or remove an article from the drafting area
    const handleToggleDraft = (articleId) => {
        setDraftingArticleIds(prevIds =>
            prevIds.includes(articleId)
              ? prevIds.filter(id => id !== articleId)
              : [...prevIds, articleId]
        );
    };

    // Handler for the "Send for review" button
    const handleSendForReview = () => {
        setDraftingArticleIds([]);
    };

    // Memoized calculation to filter articles based on selected criteria
    const filteredArticles = useMemo(() => {
        const now = new Date();
        const timeFilterMilliseconds = timeFilterHours * 60 * 60 * 1000;
        const cutoffDate = new Date(now.getTime() - timeFilterMilliseconds);

        return articles.filter(article => {
            const articleDate = new Date(article.datetime);
            if (articleDate < cutoffDate) {
                return false;
            }
            const priorityMatch = selectedPriorities.length === 0 || selectedPriorities.includes(article.priority);
            const tagMatch = selectedTags.length === 0 || article.tags.some(tag => selectedTags.includes(tag));
            return priorityMatch && tagMatch;
        });
    }, [articles, selectedTags, selectedPriorities, timeFilterHours]);

    return (
        <div className="bg-slate-50 min-h-screen font-sans text-slate-900">
            <Header />
            <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="lg:grid lg:grid-cols-12 lg:gap-8">
                    <div className="lg:col-span-8">
                        {isLoading && <p>Lade Artikel...</p>}
                        {error && <p className="text-red-500">{error}</p>}
                        {!isLoading && !error && filteredArticles.length > 0 ? (
                            filteredArticles.map(article => (
                                <NewsArticleCard 
                                    key={article.id} 
                                    article={article} 
                                    onToggleDraft={handleToggleDraft}
                                    isDrafting={draftingArticleIds.includes(article.id)}
                                />
                            ))
                        ) : (
                           !isLoading && <div className="text-center py-16"><p className="text-slate-500">Keine Artikel entsprechen den aktuellen Filtern.</p></div>
                        )}
                    </div>
                    <div className="lg:col-span-4">
                        <div className="sticky top-8 flex flex-col gap-8">
                            <TagFilter 
                                allTags={allTags}
                                selectedTags={selectedTags}
                                onTagToggle={handleTagToggle}
                                onAddNewTag={handleAddNewTag}
                                onClearFilters={handleClearFilters}
                                tagMessage={tagMessage}
                            />
                            <PriorityFilter
                                selectedPriorities={selectedPriorities}
                                onPriorityToggle={handlePriorityToggle}
                            />
                            <TimeFilter
                                hours={timeFilterHours}
                                onHoursChange={handleTimeFilterChange}
                            />
                            <SubscriptionBox onSubscribe={handleSubscribe} />
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