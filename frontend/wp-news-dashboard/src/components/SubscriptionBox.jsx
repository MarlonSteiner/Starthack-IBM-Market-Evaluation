import React, { useState } from 'react';

const SubscriptionBox = ({ onSubscribe }) => {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [isError, setIsError] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!email || !/^\S+@\S+\.\S+$/.test(email)) {
            setMessage('Bitte eine gültige E-Mail-Adresse eingeben.');
            setIsError(true);
            return;
        }

        onSubscribe(email);
        setMessage(`Benachrichtigungen für die aktuellen Filter werden an ${email} gesendet.`);
        setIsError(false);
        setEmail('');
    };

    return (
        <div className="bg-white p-6 border border-slate-200 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Benachrichtigungen abonnieren</h3>
            <form onSubmit={handleSubmit}>
                <label htmlFor="email-sub" className="block text-sm font-medium text-slate-700 mb-1">
                    Deine E-Mail
                </label>
                <div className="flex items-center space-x-2">
                    <input
                        type="email"
                        id="email-sub"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="deine.email@beispiel.com"
                        className="block w-full px-3 py-2 bg-white border border-slate-300 rounded-md placeholder-slate-400 focus:outline-none focus:ring-slate-500 focus:border-slate-500 sm:text-sm"
                    />
                    <button
                        type="submit"
                        className="px-4 py-2 text-sm font-medium text-white bg-slate-700 border border-slate-700 rounded-md hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500"
                    >
                        Hinzufügen
                    </button>
                </div>
            </form>
            <div className="h-6 mt-2">
                {message && (
                    <p className={`text-sm text-center ${isError ? 'text-red-600' : 'text-green-600'}`}>
                        {message}
                    </p>
                )}
            </div>
        </div>
    );
};

export default SubscriptionBox;