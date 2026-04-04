import { ChevronLeft, ChevronRight, Search, MessageCircle, Filter, Bot, BookOpen, Users, X, Lightbulb } from 'lucide-react';
import React, { useEffect, useState } from 'react';

const tourSteps = [
    {
        id: 'welcome',
        title: 'Welcome to RiceCatalog! 🦉',
        content: 'Welcome to Rice University\'s comprehensive academic assistant! This tutorial will guide you through all the features that will help you plan your academic journey. We\'ll explore course searching, chatting with the Rice AI advisor, and getting personalized recommendations.',
        action: 'Start Tutorial',
        icon: 'welcome'
    },
    {
        id: 'navigation-overview',
        title: 'Navigation Overview',
        content: 'The Rice Course Assistant has two main sections:\n\n🔍 "Course Catalog" - Browse and search through Rice\'s complete course database\n\n💬 "Course Chat" - Get personalized help from the Rice AI advisor\n\nYou can switch between these tabs anytime using the navigation bar.',
        target: '.nav-tabs',
        position: 'bottom',
        actionDescription: 'Click on different tabs to explore',
        icon: 'navigation'
    },
    {
        id: 'course-catalog-intro',
        title: 'Course Catalog: Your Academic Database',
        content: 'The Course Catalog is your gateway to discovering Rice University courses. Here you can search through thousands of courses, filter by department, view detailed descriptions, and plan your academic schedule.',
        target: '.nav-tab',
        position: 'bottom',
        icon: 'catalog'
    },
    {
        id: 'section-selector',
        title: 'Switch Between Course Catalog Sections',
        content: 'You can view either the current semester’s courses or the full Rice catalog. Use these buttons to toggle between:\n\n• 🍂 Fall 2025 Courses\n• 📚 All Courses\n\nTry clicking them to see how the catalog changes!',
        target: '.section-selector',
        position: 'bottom',
        icon: 'catalog'
    },
    {
        id: 'search-functionality',
        title: 'Smart Course Search',
        content: 'Use the search bar to find courses by:\n\n• Course codes (e.g., "COMP 140", "MATH 101")\n• Course titles (e.g., "calculus", "programming")\n• Keywords (e.g., "machine learning", "organic chemistry")\n• Professor names\n\nThe search is intelligent and will find relevant matches even with partial information!',
        target: '.search-container input, .search-input, [data-tour="search-input"]',
        position: 'bottom',
        actionDescription: 'Try searching for "COMP" or "calculus"',
        icon: 'search'
    },
    {
        id: 'filtering-system',
        title: 'Advanced Filtering Options',
        content: 'Narrow down your course search using powerful filters:\n\n• "Departments": Filter by specific departments like Computer Science, Mathematics, etc.\n\n• "Course Level": Find intro (100-level) or advanced (400+ level) courses\n\n• "Credits": Filter by credit hours (1-4 credits)\n\nCombine multiple filters for precise results!',
        target: '.filters-container, .filters-sidebar .filter-section, .department-filters',
        position: 'right',
        actionDescription: 'Try selecting a department or credit filter',
        icon: 'filter'
    },
    {
        id: 'course-details',
        title: 'Detailed Course Information',
        content: 'Each course card shows essential information:\n\n• "Course Code & Title": Official course identifier and name\n• "Credits": How many credit hours the course is worth\n• "Description": What you\'ll learn and course content\n• "Prerequisites": Required courses you need before taking this\n• "Instructor": Who teaches the course\n• "Meeting Times": When the course meets\n\nClick "View Details" for complete information!',
        target: '.course-card, .view-details-btn',
        position: 'top',
        actionDescription: 'Click "View Details" on any course card',
        icon: 'details'
    },
    {
        id: 'course-chat-intro',
        title: 'Course Chat: Your AI Academic Advisor',
        content: 'The Course Chat is where you get personalized academic guidance! Chat with the specialized AI advisor who can help with course selection, degree planning, prerequisites, and academic questions. It\'s like having a knowledgeable advisor available 24/7.',
        target: '.nav-tab[data-tab="chat"]',
        position: 'bottom',
        action: 'Try Course Chat',
        icon: 'chat'
    },
    {
        id: 'chat-examples',
        title: 'What You Can Ask Your Advisor',
        content: 'Your AI advisors can help with:\n\n📚 "Course Planning": "What courses should I take for a CS major?"\n🔗 "Prerequisites": "What do I need before taking COMP 440?"\n\🎯 "Career Planning": "What courses prepare me for medical school?"\n\nAsk questions in natural language - no special commands needed!',
        target: '.message-input, .input-container textarea',
        position: 'top',
        actionDescription: 'Try asking: "What CS courses should I take as a beginner?"',
        icon: 'examples'
    },
    {
        id: 'chat-features',
        title: 'Chat Features & Tips',
        content: 'Make the most of your chat experience:\n\n⚡ "Quick Responses": Get instant answers from the course database\n📊 "Detailed Analysis": Ask for in-depth course comparisons\n🔄 "Follow-up Questions": Build on previous answers\n\n**Pro Tip**: Be specific! "Show me beginner-friendly CS courses" gets better results than just "CS courses".',
        target: '.chat-container, .messages-container',
        position: 'left',
        action: 'Continue',
        icon: 'features'
    },
    {
        id: 'completion',
        title: 'You\'re Ready to Explore! 🎉',
        content: 'Congratulations! You now know how to:\n\n✅ Search and filter the course catalog\n✅ Chat with the specialized AI advisor\n✅ Get personalized course recommendations\n✅ Use advanced features\n\nReady to start your academic journey?\n Try searching for courses in your field or ask an advisor about degree requirements.\n Welcome to Rice Course Assistant!',
        action: 'Start Exploring',
        icon: 'completion'
    },
];

export const AppTutorial = ({ isOpen, onClose, onComplete, onNavigateToTab }) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [highlightedElement, setHighlightedElement] = useState(null);
    const [userHasInteracted, setUserHasInteracted] = useState({});
    const [spotlightPosition, setSpotlightPosition] = useState(null);

    // Reset to step 0 when tour opens
    useEffect(() => {
        if (isOpen) {
            setCurrentStep(0);
            setUserHasInteracted({});
        } else {
        }
    }, [isOpen]);

    // Handle navigation for specific steps
    useEffect(() => {
        if (!isOpen) return;

        const currentTourStep = tourSteps[currentStep];
        
        // Auto-navigate to appropriate tab for certain steps
        if (onNavigateToTab) {
            if (currentTourStep.id === 'course-catalog-intro' || 
                currentTourStep.id === 'search-functionality' || 
                currentTourStep.id === 'filtering-system' || 
                currentTourStep.id === 'course-details') {
                onNavigateToTab('catalog');
            } else if (currentTourStep.id === 'course-chat-intro' || 
                       currentTourStep.id === 'chat-examples' || 
                       currentTourStep.id === 'chat-features') {
                onNavigateToTab('chat');
            }
        }
    }, [currentStep, isOpen, onNavigateToTab]);

    // Listen for user interactions and auto-advance tour
    useEffect(() => {
        if (!isOpen) return;

        const checkInteractions = () => {
            const currentTourStep = tourSteps[currentStep];

            switch (currentTourStep.id) {
                case 'navigation-overview':
                    // Check if user clicked on nav tabs
                    const navTabs = document.querySelectorAll('.nav-tab');
                    if (navTabs.length > 0) {
                        setUserHasInteracted(prev => ({ ...prev, 'navigation-overview': true }));
                    }
                    break;

                case 'search-functionality':
                    // Check if user interacted with search
                    const searchInputs = document.querySelectorAll('.search-container input, .search-input, input[placeholder*="search" i]');
                    const hasSearchValue = Array.from(searchInputs).some(input => 
                        input.value.length > 0
                    );
                    if (hasSearchValue) {
                        setUserHasInteracted(prev => ({ ...prev, 'search-functionality': true }));
                    }
                    break;

                case 'filtering-system':
                    // Check if user selected any filters
                    const checkedFilters = document.querySelectorAll('input[type="checkbox"]:checked, select option:checked');
                    const selectedFilters = document.querySelectorAll('.filter-btn.active, .section-btn.active');
                    if (checkedFilters.length > 0 || selectedFilters.length > 0) {
                        setUserHasInteracted(prev => ({ ...prev, 'filtering-system': true }));
                    }
                    break;

                case 'course-details':
                    // Check if user clicked view details or opened a modal
                    const modals = document.querySelectorAll('.modal, .course-modal, [role="dialog"]');
                    if (modals.length > 0) {
                        setUserHasInteracted(prev => ({ ...prev, 'course-details': true }));
                    }
                    break;

                case 'chat-examples':
                    // Check if user typed in chat input
                    const chatInputs = document.querySelectorAll('.message-input, textarea[placeholder*="advisor" i]');
                    const hasChatInput = Array.from(chatInputs).some(input => 
                        input.value.length > 0
                    );
                    if (hasChatInput) {
                        setUserHasInteracted(prev => ({ ...prev, 'chat-examples': true }));
                    }
                    break;

                case 'user-profile':
                    // Check if user profile was updated
                    const profileInputs = document.querySelectorAll('input[placeholder*="major" i], select[name*="major" i]');
                    const hasProfileInput = Array.from(profileInputs).some(input => 
                        input.value.length > 0
                    );
                    if (hasProfileInput) {
                        setUserHasInteracted(prev => ({ ...prev, 'user-profile': true }));
                    }
                    break;

                default:
                    // Auto-mark non-interactive steps as completed
                    if (!currentTourStep.waitForAction) {
                        setUserHasInteracted(prev => ({ ...prev, [currentTourStep.id]: true }));
                    }
                    break;
            }
        };

        const interval = setInterval(checkInteractions, 500);
        checkInteractions(); // Check immediately

        return () => clearInterval(interval);
    }, [isOpen, currentStep]);

    // Temporarily unblur elements during tour
    useEffect(() => {
        if (!isOpen) return;

        const style = document.createElement('style');
        style.id = 'app-tutorial-unblur';
        style.textContent = `
            .app-tutorial-active {
                pointer-events: auto !important;
                user-select: auto !important;
            }
            
            .app-tutorial-active * {
                filter: none !important;
                pointer-events: auto !important;
            }
            
            @keyframes pulse {
                0%, 100% {
                    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
                }
                50% {
                    box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
                }
            }
            
            .tutorial-highlight {
                position: relative !important;
                z-index: 60 !important;
                animation: pulse 2s infinite !important;
                border-radius: 8px !important;
            }
        `;
        document.head.appendChild(style);
        document.body.classList.add('app-tutorial-active');

        return () => {
            const styleElement = document.getElementById('app-tutorial-unblur');
            if (styleElement) {
                styleElement.remove();
            }
            document.body.classList.remove('app-tutorial-active');
        };
    }, [isOpen]);

    // Highlight target elements
    useEffect(() => {
        if (!isOpen) return;

        const step = tourSteps[currentStep];
        if (step.target) {
            setTimeout(() => {
                const element = document.querySelector(step.target);
                if (element) {
                    setHighlightedElement(element);
                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    element.classList.add('tutorial-highlight');
                    
                    const rect = element.getBoundingClientRect();
                    setSpotlightPosition({
                        top: rect.top - 8,
                        left: rect.left - 8,
                        width: rect.width + 16,
                        height: rect.height + 16,
                    });
                }
            }, 100);
        } else {
            setHighlightedElement(null);
            setSpotlightPosition(null);
        }

        return () => {
            if (highlightedElement) {
                highlightedElement.classList.remove('tutorial-highlight');
            }
        };
    }, [currentStep, isOpen, highlightedElement]);

    // Update spotlight position when element moves
    useEffect(() => {
        if (!isOpen || !highlightedElement) {
            setSpotlightPosition(null);
            return;
        }

        const updatePosition = () => {
            const rect = highlightedElement.getBoundingClientRect();
            setSpotlightPosition({
                top: rect.top - 8,
                left: rect.left - 8,
                width: rect.width + 16,
                height: rect.height + 16,
            });
        };

        updatePosition();

        const debouncedUpdate = () => setTimeout(updatePosition, 10);
        window.addEventListener('scroll', debouncedUpdate);
        window.addEventListener('resize', debouncedUpdate);

        const observer = new MutationObserver(debouncedUpdate);
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
        });

        return () => {
            window.removeEventListener('scroll', debouncedUpdate);
            window.removeEventListener('resize', debouncedUpdate);
            observer.disconnect();
        };
    }, [isOpen, highlightedElement]);

    // Handle escape key
    useEffect(() => {
        if (!isOpen) return;

        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose]);

    const handleNext = () => {
        const currentTourStep = tourSteps[currentStep];

        if (currentTourStep.waitForAction && currentTourStep.id) {
            setUserHasInteracted(prev => ({ ...prev, [currentTourStep.id]: true }));
        }

        if (currentStep < tourSteps.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            if (onNavigateToTab) {
                onNavigateToTab('catalog');
                setTimeout(() => {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }, 100);
            }
            onComplete();
        }
    };

    const handlePrevious = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1);
        }
    };

    const handleStepClick = (index) => {
        setCurrentStep(index);
    };

    const getStepIcon = (iconType) => {
        const iconMap = {
            welcome: <Lightbulb className="w-6 h-6 text-white" />,
            navigation: <BookOpen className="w-6 h-6 text-white" />,
            catalog: <Search className="w-6 h-6 text-white" />,
            search: <Search className="w-6 h-6 text-white" />,
            filter: <Filter className="w-6 h-6 text-white" />,
            details: <BookOpen className="w-6 h-6 text-white" />,
            chat: <MessageCircle className="w-6 h-6 text-white" />,
            advisor: <Users className="w-6 h-6 text-white" />,
            examples: <Bot className="w-6 h-6 text-white" />,
            features: <MessageCircle className="w-6 h-6 text-white" />,
            profile: <Users className="w-6 h-6 text-white" />,
            advanced: <Bot className="w-6 h-6 text-white" />,
            completion: <Lightbulb className="w-6 h-6 text-white" />
        };
        return iconMap[iconType] || <Lightbulb className="w-6 h-6 text-white" />;
    };

    if (!isOpen) return null;

    const currentTourStep = tourSteps[currentStep];
    const isFirstStep = currentStep === 0;
    const isLastStep = currentStep === tourSteps.length - 1;
    const canProceed = true;

    return (
        <div className="tutorial-modal-overlay">
            {/* Background overlay - separate from modal content */}
            <div className="tutorial-modal-bg" />

            {/* Spotlight effect for target element */}
            {spotlightPosition && currentTourStep.target && (
                <div
                    className="tutorial-modal-spotlight"
                    style={{
                        top: spotlightPosition.top,
                        left: spotlightPosition.left,
                        width: spotlightPosition.width,
                        height: spotlightPosition.height,
                        background: 'transparent',
                        boxShadow: `
                            0 0 0 8px rgba(255, 255, 255, 0.1),
                            0 0 0 9999px rgba(0, 0, 0, 0.4)
                        `,
                        borderRadius: '12px',
                        transition: 'all 0.3s ease-in-out',
                        position: 'fixed',
                        pointerEvents: 'none',
                        zIndex: 10000,
                    }}
                />
            )}

            {/* Step indicators */}
            <div className="tutorial-modal-step-indicators">
                <div className="tutorial-modal-step-indicator-list">
                    {tourSteps.map((_, index) => (
                        <button
                            key={index}
                            onClick={() => handleStepClick(index)}
                            className={`tutorial-modal-step-dot${index === currentStep ? ' active' : ''}${index < currentStep ? ' completed' : ''}`}
                            title={`Step ${index + 1}: ${tourSteps[index].title}`}
                        />
                    ))}
                </div>
            </div>

            {/* Main tour modal */}
            <div className="tutorial-modal-content">
                {/* Header */}
                <div className="tutorial-modal-header">
                    <div className="tutorial-modal-header-left">
                        <div className="tutorial-modal-header-icon">
                            {getStepIcon(currentTourStep.icon || 'default')}
                        </div>
                        <div>
                            <h3 className="tutorial-modal-title">{currentTourStep.title}</h3>
                            <p className="tutorial-modal-step">Step {currentStep + 1} of {tourSteps.length}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="tutorial-modal-close"
                        title="Close tutorial"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Content */}
                <div className="tutorial-modal-body">
                    <p className="tutorial-modal-content-text">
                        {currentTourStep.content}
                    </p>

                </div>

                {/* Footer */}
                <div className="tutorial-modal-footer">
                    <div className="tutorial-modal-footer-left">
                        {!isFirstStep && (
                            <button
                                onClick={handlePrevious}
                                className="tutorial-modal-footer-btn tutorial-modal-footer-prev"
                            >
                                <ChevronLeft className="w-4 h-4" />
                                Previous
                            </button>
                        )}
                    </div>

                    <button
                        onClick={handleNext}
                        disabled={false}
                        className={`tutorial-modal-footer-btn tutorial-modal-footer-next${canProceed || !currentTourStep.waitForAction ? ' active' : ' disabled'}`}
                    >
                        {currentTourStep.action || (isLastStep ? 'Finish' : 'Next')}
                        {!isLastStep && <ChevronRight className="w-4 h-4" />}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AppTutorial; 