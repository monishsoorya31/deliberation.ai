
import React, { useState, useEffect, useRef } from 'react';
import { startDeliberation, getStreamUrl, getConversationHistory } from '../services/api';
import MessageItem from './MessageItem';

interface ChatInterfaceProps {
    apiKeys: { openai: string; gemini: string; deepseek: string };
    maxRounds: number;
    onReset: () => void;
}

interface Message {
    id?: string;
    agent_name: string;
    content: string;
    round_number: number;
    timestamp?: string;
    is_internal_thought?: boolean;
    type?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ apiKeys, maxRounds, onReset }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [question, setQuestion] = useState('');
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [currentRound, setCurrentRound] = useState(0);
    const eventSourceRef = useRef<EventSource | null>(null);

    const syncHistory = async (convoId: string) => {
        try {
            const history = await getConversationHistory(convoId);
            if (history && history.length > 0) {
                setMessages(history);
            }
        } catch (err) {
            console.error("Failed to sync history:", err);
        }
    };

    const handleStart = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!question.trim()) return;

        setLoading(true);
        setMessages([]);
        setCurrentRound(1); // Assume starts at 1

        try {
            // Add user's question to messages immediately for feedback
            const userMsg: Message = {
                agent_name: 'user',
                content: question,
                round_number: 0,
                is_internal_thought: false
            };
            setMessages([userMsg]);
            const currentQ = question; // Capture current question
            setQuestion(''); // Clear input

            const response = await startDeliberation(currentQ, apiKeys, maxRounds);
            const convoId = response.conversation_id;
            setConversationId(convoId);

            // Connect to Stream
            const url = getStreamUrl(convoId);
            const source = new EventSource(url);
            eventSourceRef.current = source;

            source.onopen = () => {
                console.log('SSE connection opened');
            };

            source.addEventListener('message', async (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === 'token') {
                        setMessages((prev) => {
                            // Find existing message for this specific agent and round
                            const msgIndex = prev.findIndex(m => m.agent_name === data.agent && m.round_number === data.round);

                            if (msgIndex !== -1) {
                                const newMessages = [...prev];
                                const existingMsg = newMessages[msgIndex];
                                newMessages[msgIndex] = { ...existingMsg, content: existingMsg.content + data.content };
                                return newMessages;
                            } else {
                                // Start a new message for this agent
                                return [
                                    ...prev,
                                    {
                                        agent_name: data.agent,
                                        content: data.content,
                                        round_number: data.round || 0,
                                        is_internal_thought: false
                                    }
                                ];
                            }
                        });
                    } else if (data.type === 'message' || !data.type) {
                        // Check if message already exists (we might have streamed it)
                        setMessages((prev) => {
                            const exists = prev.some(m => m.agent_name === data.agent && m.round_number === data.round && m.content.length >= data.content.length);
                            if (exists) return prev;

                            return [...prev, {
                                agent_name: data.agent,
                                content: data.content,
                                round_number: data.round || 0,
                                is_internal_thought: false
                            }];
                        });
                    } else if (data.type === 'round_update') {
                        setCurrentRound(data.round);
                    } else if (data.type === 'final') {
                        // Final answer received
                        await syncHistory(convoId);
                        setLoading(false);
                        source.close();
                    } else if (data.type === 'error') {
                        console.error("Server Error:", data.message);
                        await syncHistory(convoId);
                        setLoading(false);
                        source.close();
                    }

                } catch (err) {
                    console.error('Error parsing SSE data', err);
                }
            });

            source.onerror = async (err) => {
                console.error('SSE error', err);
                await syncHistory(convoId);
                source.close();
                setLoading(false);
            };

        } catch (err) {
            console.error('Failed to start deliberation', err);
            setLoading(false);
        }
    };

    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    const [showReasoning, setShowReasoning] = useState(true);

    // ... (existing code: handleStart logic remains)

    const filteredMessages = messages.filter(msg => {
        if (showReasoning) return true;
        // Always show User and Arbiter (Final Answer)
        const name = msg.agent_name.toLowerCase();
        if (name === 'user' || name === 'arbiter') return true;
        return false;
    });

    return (
        <div className="flex flex-col h-screen bg-slate-50 text-slate-900 overflow-hidden">
            {/* Glass Header */}
            <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 p-4 flex justify-between items-center shrink-0 z-20">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-sky-600 rounded-lg flex items-center justify-center">
                            <span className="text-white font-black text-xl">D</span>
                        </div>
                        <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">Deliberation Hub</h1>
                    </div>

                    <div className="h-6 w-px bg-slate-200 hidden sm:block"></div>

                    <label className="flex items-center gap-3 cursor-pointer group">
                        <div className="relative">
                            <input
                                type="checkbox"
                                checked={showReasoning}
                                onChange={(e) => setShowReasoning(e.target.checked)}
                                className="sr-only peer"
                            />
                            <div className="w-10 h-6 bg-slate-200 rounded-full peer peer-checked:bg-sky-500 transition-colors"></div>
                            <div className="absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-4 shadow-sm"></div>
                        </div>
                        <span className="text-sm font-semibold text-slate-600 group-hover:text-slate-900 transition-colors select-none">Show Deliberation</span>
                    </label>
                </div>

                <div className="flex items-center gap-4">
                    {conversationId && (
                        <span className="hidden md:inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                            ID: {conversationId.split('-')[0]}
                        </span>
                    )}
                    <button
                        onClick={onReset}
                        className="text-sm font-bold text-red-500 hover:bg-red-50 px-3 py-2 rounded-lg transition-colors"
                    >
                        Reset Keys
                    </button>
                </div>
            </header>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8 max-w-5xl mx-auto w-full">
                {messages.length === 0 && !loading && (
                    <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-50 max-w-md mx-auto">
                        <div className="w-16 h-16 bg-slate-200 rounded-2xl flex items-center justify-center">
                            <span className="text-2xl">⚡</span>
                        </div>
                        <h3 className="text-lg font-bold">Start a Multi-Agent Debate</h3>
                        <p className="text-sm">Enter a topic or question below. Gemini and DeepSeek will deliberate to find the most accurate consensus.</p>
                    </div>
                )}

                {filteredMessages.map((msg, idx) => (
                    <MessageItem key={idx} message={msg} />
                ))}

                {loading && (
                    <div className="flex flex-col items-center justify-center p-8 space-y-4">
                        <div className="flex gap-1">
                            <div className="w-2 h-2 bg-sky-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                            <div className="w-2 h-2 bg-sky-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                            <div className="w-2 h-2 bg-sky-500 rounded-full animate-bounce"></div>
                        </div>
                        <span className="text-sm font-bold text-slate-500 uppercase tracking-tighter">
                            Agents Deliberating (Round {currentRound})
                        </span>
                    </div>
                )}
                <div className="h-2" />
            </div>

            {/* Input Bar */}
            <div className="p-6 bg-white border-t border-slate-200 shrink-0 z-20">
                <form onSubmit={handleStart} className="max-w-4xl mx-auto relative group">
                    <input
                        type="text"
                        className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-4 pl-6 pr-32 focus:ring-4 focus:ring-sky-500/10 focus:border-sky-500 outline-none transition-all text-lg shadow-sm group-hover:bg-white"
                        placeholder="What would you like the agents to deliberate on?"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        disabled={loading}
                    />
                    <div className="absolute right-2 top-2 bottom-2 p-1">
                        <button
                            type="submit"
                            disabled={loading || !question.trim()}
                            className="h-full px-6 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 disabled:bg-slate-200 disabled:text-slate-400 transition-all active:scale-95 flex items-center gap-2"
                        >
                            {loading ? 'Thinking' : 'Send'}
                            {!loading && <span className="text-lg">↵</span>}
                        </button>
                    </div>
                </form>
                <p className="text-center text-[10px] text-slate-400 mt-4 uppercase font-bold tracking-widest">
                    Multi-Perspective Synthesis Engine v1.0
                </p>
            </div>
        </div>
    );
};

export default ChatInterface;
