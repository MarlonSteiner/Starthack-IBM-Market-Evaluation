import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:3001/api';

const SubscriptionForm = ({ activeTags }) => {
    const [email, setEmail] = useState('');
    const [customQuery, setCustomQuery] = useState('');
    const [subType, setSubType] = useState('tags'); // 'tags' or 'custom'
    const [message, setMessage] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');

        if (!email) {
            setMessage('Error: Please enter a valid email address.');
            return;
        }

        const subscriptionData = {
            email,
            type: subType,
            query: subType === 'tags' ? activeTags : customQuery,
        };
        
        if (subscriptionData.query.length === 0) {
            setMessage('Error: Please select tags or enter a custom query.');
            return;
        }

        try {
            await axios.post(`${API_BASE_URL}/subscribe`, subscriptionData);
            setMessage(`Success! A confirmation email has been sent to ${email}.`);
            setEmail('');
            setCustomQuery('');
        } catch (error) {
            setMessage('Error: Could not process subscription. Please try again later.');
            console.error(error);
        }
    };

    return (
        <div className="mt-8 bg-white p-6 border border-gray-200 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Subscribe to Alerts</h3>
            
            <form onSubmit={handleSubmit}>
                <div className="mb-4">
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Your Email</label>
                    <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="your.email@example.com"
                        className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-md placeholder-gray-400 focus:outline-none focus:ring-slate-500 focus:border-slate-500 sm:text-sm"
                    />
                </div>

                <div className="flex border border-gray-200 rounded-md mb-4">
                    <button type="button" onClick={() => setSubType('tags')} className={`flex-1 p-2 text-sm font-medium ${subType === 'tags' ? 'bg-slate-700 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}>By Selected Tags</button>
                    <button type="button" onClick={() => setSubType('custom')} className={`flex-1 p-2 text-sm font-medium ${subType === 'custom' ? 'bg-slate-700 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}>By Custom Query</button>
                </div>

                {subType === 'tags' && (
                    <div className="p-3 bg-slate-50 rounded-md text-sm text-gray-600">
                        {activeTags.length > 0 ? `Tags: ${activeTags.join(', ')}` : "Please select tags from the filter above."}
                    </div>
                )}

                {subType === 'custom' && (
                     <div>
                        <label htmlFor="custom-query" className="block text-sm font-medium text-gray-700 mb-1">Custom Query</label>
                        <input
                            type="text"
                            id="custom-query"
                            value={customQuery}
                            onChange={(e) => setCustomQuery(e.target.value)}
                            placeholder="e.g., 'interest rates' or 'Innovate Corp'"
                            className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-md placeholder-gray-400 focus:outline-none focus:ring-slate-500 focus:border-slate-500 sm:text-sm"
                        />
                    </div>
                )}
                
                <button type="submit" className="w-full mt-4 px-4 py-2 text-sm font-medium text-white bg-slate-700 border border-slate-700 rounded-md hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500">
                    Subscribe
                </button>

                {message && <p className={`mt-3 text-sm ${message.startsWith('Error') ? 'text-red-600' : 'text-green-600'}`}>{message}</p>}
            </form>
        </div>
    );
};

export default SubscriptionForm;