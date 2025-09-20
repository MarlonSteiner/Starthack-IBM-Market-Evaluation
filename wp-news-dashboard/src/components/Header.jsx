import React from 'react';
import marketRoosterLogo from '../images/MarketRooster.png';

const Header = () => (
    <header className="bg-white border-b border-slate-200">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-20">
                <div className="flex items-center space-x-4"> {/* Mehr Platz */}
                    <img 
                        src={marketRoosterLogo} 
                        alt="MarketRooster Logo" 
                        className="h-12 w-auto"
                    />
                    {/* Schriftstärke von 'font-light' auf 'font-normal' erhöht */}
                    <span className="text-xl font-normal text-slate-800 hidden sm:inline">MarketRooster</span>
                </div>
                <div className="flex items-center space-x-6">
                    {/* Navigationslinks erben 'font-medium' */}
                    <nav className="hidden md:flex space-x-6">
                        {['Dashboard', 'Publikationen', 'Team und Kontakt', 'Podcast'].map(item => (
                            <a href="#" key={item} className="text-slate-600 hover:text-slate-900 text-sm transition-colors duration-200">
                                {item}
                            </a>
                        ))}
                    </nav>
                    <div className="flex items-center space-x-2 text-sm text-slate-500 border-l border-slate-300 pl-4">
                       <a href="#" className="font-semibold text-slate-800">Deutsch</a>
                       <span>/</span>
                       <a href="#" className="hover:text-slate-800">English</a>
                    </div>
                </div>
            </div>
        </div>
    </header>
);

export default Header;