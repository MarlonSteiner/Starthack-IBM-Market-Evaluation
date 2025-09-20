import React from 'react';
import NewsArticleCard from '../components/NewsArticleCard';
import TagFilter from '../components/TagFilter';
import PriorityFilter from '../components/PriorityFilter';
import TimeFilter from '../components/TimeFilter';
import SubscriptionBox from '../components/SubscriptionBox';
import DraftingArea from '../components/DraftingArea';

const DashboardPage = ({
    isLoading, error, filteredArticles, onToggleDraft, draftingArticleIds,
    allTags, selectedTags, onTagToggle, onAddNewTag, onClearFilters, tagMessage,
    selectedPriorities, onPriorityToggle,
    timeFilterHours, onTimeFilterChange,
    onSubscribe,
    articles, onSendForReview
}) => {
    return (
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="lg:grid lg:grid-cols-12 lg:gap-8">
                <div className="lg:col-span-8">
                    {isLoading && <p>Lade Artikel...</p>}
                    {error && <p className="text-red-500">{error}</p>}
                    {!isLoading && !error && filteredArticles.length > 0 ? (
                        filteredArticles.map(article => (
                            <NewsArticleCard
                                key={article.id}
                                article={article}
                                onToggleDraft={onToggleDraft}
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
                            onTagToggle={onTagToggle}
                            onAddNewTag={onAddNewTag}
                            onClearFilters={onClearFilters}
                            tagMessage={tagMessage}
                        />
                        <PriorityFilter
                            selectedPriorities={selectedPriorities}
                            onPriorityToggle={onPriorityToggle}
                        />
                        <TimeFilter
                            hours={timeFilterHours}
                            onHoursChange={onTimeFilterChange}
                        />
                        <SubscriptionBox onSubscribe={onSubscribe} />
                        <DraftingArea
                            articles={articles}
                            draftingArticleIds={draftingArticleIds}
                            onSendForReview={onSendForReview}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;