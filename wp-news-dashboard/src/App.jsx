import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';

// Import components
import Header from './components/Header';
import TagFilter from './components/TagFilter';
import PriorityFilter from './components/PriorityFilter';
import TimeFilter from './components/TimeFilter'; // <-- Import the new component
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
    const [tagMessage, setTagMessage] = useState('');
    const [selectedPriorities, setSelectedPriorities] = useState([]);
    const [timeFilterHours, setTimeFilterHours] = useState(72); // <-- New state for time filter

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [articlesResponse, tagsResponse] = await Promise.all([
                    axios.get(`${API_BASE_URL}/articles`),
                    axios.get(`${API_BASE_URL}/tags`)
                ]);
                // Sort articles by date descending on initial load
                const sortedArticles = articlesResponse.data.sort((a, b) => new Date(b.datetime) - new Date(a.datetime));
                setArticles(sortedArticles);
                setAllTags(tagsResponse.data);
            } catch (err) {
                setError('Failed to load data from the server.');
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    const handlePriorityToggle = (priority) => {
        setSelectedPriorities(prev =>
            prev.includes(priority)
            ? prev.filter(p => p !== priority)
            : [...prev, priority]
        );
    };

    // New handler for the time filter
    const handleTimeFilterChange = (hours) => {
        setTimeFilterHours(hours);
    };

    const handleTagToggle = (tagName) => {
        setSelectedTags(prevTags =>
            prevTags.includes(tagName)
            ? prevTags.filter(t => t !== tagName)
            : [...prevTags, tagName]
        );
    };

    const handleClearFilters = () => {
        setSelectedTags([]);
        setSelectedPriorities([]);
        setTimeFilterHours(72); // Also reset time filter
    };

    const handleAddNewTag = async (tagName) => {
        setTagMessage('');
        try {
            const response = await axios.post(`${API_BASE_URL}/tags/process`, { name: tagName });
            const { newTag, updatedArticles, allTags: updatedAllTags } = response.data;
            setArticles(updatedArticles);
            setAllTags(updatedAllTags);
            setSelectedTags([newTag.name]);
            const matches = updatedArticles.filter(article => article.tags.includes(newTag.name));
            if (matches.length === 0) {
                setTagMessage('Could not find tag related news');
                setTimeout(() => {
                    setTagMessage('');
                }, 3000);
            }
        } catch (err) {
            console.error("API Call Failed:", err.response || err);
            alert("Error: Could not add the new tag. Check console (F12) for details.");
        }
    };

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

    const filteredArticles = useMemo(() => {
        const now = new Date();
        const timeFilterMilliseconds = timeFilterHours * 60 * 60 * 1000;
        const cutoffDate = new Date(now.getTime() - timeFilterMilliseconds);

        let tempArticles = articles;

        // Apply time filter
        tempArticles = tempArticles.filter(article => {
            const articleDate = new Date(article.datetime);
            return articleDate >= cutoffDate;
        });

        // Apply tag filter
        if (selectedTags.length > 0) {
            tempArticles = tempArticles.filter(article =>
                article.tags.some(tag => selectedTags.includes(tag))
            );
        }

        // Apply priority filter
        if (selectedPriorities.length > 0) {
            tempArticles = tempArticles.filter(article =>
                selectedPriorities.includes(article.priority)
            );
        }

        return tempArticles;
    }, [articles, selectedTags, selectedPriorities, timeFilterHours]); // <-- Add timeFilterHours dependency

    return (
        <div className="bg-slate-50 min-h-screen font-sans text-slate-900">
            <Header />
            <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="lg:grid lg:grid-cols-12 lg:gap-8">
                    <div className="lg:col-span-8">
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
                            <div className="text-center py-16">
                                <p className="text-slate-500">No articles match the current filters.</p>
                            </div>
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
                            {/* Render the new component here */}
                            <TimeFilter
                                hours={timeFilterHours}
                                onHoursChange={handleTimeFilterChange}
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