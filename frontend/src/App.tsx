
import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import ApiKeyModal from './components/ApiKeyModal';

const App: React.FC = () => {
    const [apiKeys, setApiKeys] = useState<{ openai: string; gemini: string; deepseek: string } | null>(null);
    const [maxRounds, setMaxRounds] = useState(3);

    const handleSaveConfig = (keys: { openai: string; gemini: string; deepseek: string }, rounds: number) => {
        setApiKeys(keys);
        setMaxRounds(rounds);
    };

    const handleReset = () => {
        setApiKeys(null);
    };

    return (
        <div className="h-screen w-full">
            {!apiKeys ? (
                <ApiKeyModal onSave={handleSaveConfig} />
            ) : (
                <ChatInterface apiKeys={apiKeys} maxRounds={maxRounds} onReset={handleReset} />
            )}
        </div>
    );
};

export default App;
