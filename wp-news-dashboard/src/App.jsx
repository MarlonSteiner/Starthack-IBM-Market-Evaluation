import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';

// Die neue Komponente importieren
import Header from './components/Header';
import TagFilter from './components/TagFilter';
import PriorityFilter from './components/PriorityFilter'; // NEU
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

    // NEUER STATE für die Prioritätenfilter
    const [selectedPriorities, setSelectedPriorities] = useState([]);

    useEffect(() => {
        // ... (Datenabruf bleibt unverändert)
        const fetchData = async () => {
            try {
                const [articlesResponse, tagsResponse] = await Promise.all([
                    axios.get(`${API_BASE_URL}/articles`),
                    axios.get(`${API_BASE_URL}/tags`)
                ]);
                setArticles(articlesResponse.data);
                setAllTags(tagsResponse.data);
            } catch (err) { setError('Failed to load data from the server.'); } 
            finally { setIsLoading(false); }
        };
        fetchData();
    }, []);
    
    // NEUER HANDLER für die Prioritäten
    const handlePriorityToggle = (priority) => {
        setSelectedPriorities(prev =>
            prev.includes(priority)
            ? prev.filter(p => p !== priority)
            : [...prev, priority]
        );
    };

    const handleTagToggle = (tagName) => {
        setSelectedTags(prevTags => 
            prevTags.includes(tagName) 
            ? prevTags.filter(t => t !== tagName) 
            : [...prevTags, tagName]
        );
    };
    
    const handleClearFilters = () => setSelectedTags([]);

    const handleAddNewTag = async (tagName) => {
        // Bestehende Nachrichten löschen, bevor eine neue hinzugefügt wird
        setTagMessage('');

        try {
            const response = await axios.post(`${API_BASE_URL}/tags/process`, { name: tagName });
            const { newTag, updatedArticles, allTags: updatedAllTags } = response.data;
            
            setArticles(updatedArticles);
            setAllTags(updatedAllTags);
            setSelectedTags([newTag.name]);

            // NEUE LOGIK: Prüfen, ob der neue Tag Treffer erzielt hat
            const matches = updatedArticles.filter(article => article.tags.includes(newTag.name));
            if (matches.length === 0) {
                setTagMessage('Could not find tag related news');
                // Nachricht nach 3 Sekunden ausblenden
                setTimeout(() => {
                    setTagMessage('');
                }, 3000);
            }

        } catch(err) {
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

    // ERWEITERTE FILTERLOGIK
    const filteredArticles = useMemo(() => {
        let tempArticles = articles;

        // 1. Nach Tags filtern
        if (selectedTags.length > 0) {
            tempArticles = tempArticles.filter(article => 
                article.tags.some(tag => selectedTags.includes(tag))
            );
        }

        // 2. Nach Prioritäten filtern
        if (selectedPriorities.length > 0) {
            tempArticles = tempArticles.filter(article =>
                selectedPriorities.includes(article.priority)
            );
        }

        return tempArticles;
    }, [articles, selectedTags, selectedPriorities]); // Abhängigkeit hinzugefügt


    return (
        <div className="bg-gray-200 min-h-screen font-sans text-gray-900">
            <Header />
            <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
                
                <div className="lg:grid lg:grid-cols-12 lg:gap-8">
                    <div className="lg:col-span-8">
                       {/* ... (Nachrichtenanzeige unverändert) ... */}
                       {!isLoading && !error && filteredArticles.map(article => (
                           <NewsArticleCard 
                                key={article.id} 
                                article={article} 
                                onToggleDraft={handleToggleDraft}
                                isDrafting={draftingArticleIds.includes(article.id)}
                            />
                       ))}
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
                            {/* NEUE KOMPONENTE HIER EINGEFÜGT */}
                             <PriorityFilter
                                selectedPriorities={selectedPriorities}
                                onPriorityToggle={handlePriorityToggle}
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