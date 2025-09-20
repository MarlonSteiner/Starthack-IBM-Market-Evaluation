import React from 'react';
import { NavLink } from 'react-router-dom';
import marketRoosterLogo from '../images/MarketRooster.png';

const Header = ({ reviewCount }) => {
    const navLinkClasses = "text-slate-600 hover:text-slate-900 text-sm transition-colors duration-200";
    const activeLinkClasses = { color: '#0f172a' }; // slate-900

    return (
        <header className="bg-white border-b border-slate-200">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-20">
                    <div className="flex items-center space-x-4">
                        <img src={marketRoosterLogo} alt="MarketRooster Logo" className="h-12 w-auto" />
                        <span className="text-xl font-normal text-slate-800 hidden sm:inline">MarketRooster</span>
                    </div>
                    <div className="flex items-center space-x-6">
                        <nav className="hidden md:flex space-x-6 items-center">
                            
                            <NavLink
                                to="/review"
                                className={navLinkClasses}
                                style={({ isActive }) => isActive ? activeLinkClasses : undefined}
                            >
                                Überprüfung
                                {reviewCount > 0 && (
                                    <span className="notification-badge">{reviewCount}</span>
                                )}
                            </NavLink>
                        </nav>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;