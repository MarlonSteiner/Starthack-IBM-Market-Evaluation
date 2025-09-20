import React from 'react';

const RelevanceBadge = ({ relevance }) => {
    const baseClasses = "px-2.5 py-1 text-xs font-semibold rounded-full inline-block";
    const colorClasses = {
        High: "bg-red-100 text-red-800",
        Medium: "bg-yellow-100 text-yellow-800",
        Low: "bg-blue-100 text-blue-800"
    };
    return <span className={`${baseClasses} ${colorClasses[relevance]}`}>{relevance} Relevance</span>;
};

export default RelevanceBadge;