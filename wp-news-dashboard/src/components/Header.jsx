import React from 'react';

const Header = () => (
    <header className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-20">
                <div className="flex items-center space-x-3">
                    <div className="font-light text-3xl text-gray-600 tracking-wider">
                        W<span className="text-gray-400">&</span>P
                    </div>
                    <span className="text-xl font-light text-gray-800 hidden sm:inline">Early-Warning System</span>
                </div>
                <div className="flex items-center space-x-6">
                    <nav className="hidden md:flex space-x-6">
                        {['Dashboard', 'Publikationen', 'Team und Kontakt', 'Podcast'].map(item => (
                            <a href="#" key={item} className="text-gray-600 hover:text-gray-900 text-sm font-medium transition-colors duration-200">
                                {item}
                            </a>
                        ))}
                    </nav>
                    <div className="flex items-center space-x-2 text-sm text-gray-500 border-l border-gray-300 pl-4">
                       <a href="#" className="font-semibold text-gray-800">Deutsch</a>
                       <span>/</span>
                       <a href="#" className="hover:text-gray-800">English</a>
                    </div>
                </div>
            </div>
        </div>
    </header>
);

export default Header;