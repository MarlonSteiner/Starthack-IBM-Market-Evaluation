import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Routes, Route } from 'react-router-dom';

// Seiten und Komponenten importieren
import Header from './components/Header';
import DashboardPage from './pages/DashboardPage';
import ReviewPage from './pages/ReviewPage';

const API_BASE_URL = 'http://localhost:3001/api';

function App() {
    // --- STATES ---
    const [articles, setArticles] = useState([]);
    const [allTags, setAllTags] = useState([]);
    const [selectedTags, setSelectedTags] = useState([]);
    const [selectedPriorities, setSelectedPriorities] = useState([]);
    const [draftingArticleIds, setDraftingArticleIds] = useState([]);
    const [timeFilterHours, setTimeFilterHours] = useState(72);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [tagMessage, setTagMessage] = useState('');
    const [reviewItems, setReviewItems] = useState([]);

    // --- DATENLADEN ---
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

    // --- HANDLER FÜR REVIEW-PROZESS ---
    const handleSendForReview = (compiledText, sources) => {
        const newItem = {
            id: Date.now(),
            text: compiledText,
            sources: sources || []
        };
        setReviewItems(prevItems => [...prevItems, newItem]);
        setDraftingArticleIds([]);
    };

    const handleApprove = async (itemId, text) => {
        try {
            await axios.post(`${API_BASE_URL}/approved`, { approvedText: text });
            setReviewItems(prev => prev.filter(item => item.id !== itemId));
        } catch (err) {
            console.error("Failed to save approved text:", err);
            alert("Fehler: Der akzeptierte Text konnte nicht gespeichert werden.");
        }
    };

    const handleReject = (itemId) => {
        setReviewItems(prev => prev.filter(item => item.id !== itemId));
    };

    // --- ANDERE HANDLER ---
    const handleSubscribe = async (email) => {
        try {
            const subscriptionData = { email, tags: selectedTags, priorities: selectedPriorities };
            await axios.post(`${API_BASE_URL}/subscribe`, subscriptionData);
        } catch (err) {
            console.error("Subscription failed:", err.response || err);
            alert("Fehler: Abonnement konnte nicht gespeichert werden.");
        }
    };

    const handlePriorityToggle = (priority) => {
        setSelectedPriorities(prev => prev.includes(priority) ? prev.filter(p => p !== priority) : [...prev, priority]);
    };

    const handleTimeFilterChange = (hours) => {
        setTimeFilterHours(hours);
    };

    const handleTagToggle = (tagName) => {
        setSelectedTags(prevTags => prevTags.includes(tagName) ? prevTags.filter(t => t !== tagName) : [...prevTags, tagName]);
    };
    
    const handleClearFilters = () => {
        setSelectedTags([]);
        setSelectedPriorities([]);
        setTimeFilterHours(72);
    };

    const handleAddNewTag = async (tagName) => {
        setTagMessage('');
        try {
            const response = await axios.post(`${API_BASE_URL}/tags/process`, { name: tagName });
            const { updatedArticles, allTags: updatedAllTags } = response.data;
            setArticles(updatedArticles);
            setAllTags(updatedAllTags);
            setSelectedTags([tagName]);
            const matches = updatedArticles.filter(article => article.tags && article.tags.includes(tagName));
            if (matches.length === 0) {
                setTagMessage('Keine Artikel für diesen Tag gefunden');
                setTimeout(() => setTagMessage(''), 3000);
            }
        } catch (err) {
            console.error("API Call Failed:", err.response || err);
            alert("Fehler: Neuer Tag konnte nicht verarbeitet werden. Details in der Konsole.");
        }
    };

    const handleToggleDraft = (articleId) => {
        setDraftingArticleIds(prevIds => prevIds.includes(articleId) ? prevIds.filter(id => id !== articleId) : [...prevIds, articleId]);
    };
    
    const filteredArticles = useMemo(() => {
        const now = new Date();
        const timeFilterMilliseconds = timeFilterHours * 60 * 60 * 1000;
        const cutoffDate = new Date(now.getTime() - timeFilterMilliseconds);
        return articles.filter(article => {
            const articleDate = new Date(article.datetime);
            if (articleDate < cutoffDate) return false;
            const priorityMatch = selectedPriorities.length === 0 || selectedPriorities.includes(article.priority);
            const tagMatch = selectedTags.length === 0 || article.tags.some(tag => selectedTags.includes(tag));
            return priorityMatch && tagMatch;
        });
    }, [articles, selectedTags, selectedPriorities, timeFilterHours]);

    return (
        // These classes fix the layout to the screen height for independent scrolling
        <div className="bg-slate-200 h-screen flex flex-col overflow-hidden">
            <Header reviewCount={reviewItems.length} />
            {/* This main area fills the remaining space and contains the routes */}
            <main className="flex-1 overflow-y-hidden">
                <Routes>
                    <Route
                        path="/"
                        element={
                            <DashboardPage
                                isLoading={isLoading}
                                error={error}
                                filteredArticles={filteredArticles}
                                onToggleDraft={handleToggleDraft}
                                draftingArticleIds={draftingArticleIds}
                                allTags={allTags}
                                selectedTags={selectedTags}
                                onTagToggle={handleTagToggle}
                                onAddNewTag={handleAddNewTag}
                                onClearFilters={handleClearFilters}
                                tagMessage={tagMessage}
                                selectedPriorities={selectedPriorities}
                                onPriorityToggle={handlePriorityToggle}
                                timeFilterHours={timeFilterHours}
                                onTimeFilterChange={handleTimeFilterChange}
                                onSubscribe={handleSubscribe}
                                articles={articles}
                                onSendForReview={handleSendForReview}
                            />
                        }
                    />
                    <Route
                        path="/review"
                        element={
                            <ReviewPage
                                items={reviewItems}
                                onApprove={handleApprove}
                                onReject={handleReject}
                            />
                        }
                    />
                </Routes>
            </main>
        </div>
    );
}

export default App;