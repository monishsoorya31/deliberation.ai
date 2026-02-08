
import React from 'react';

interface Message {
    agent_name: string;
    content: string;
    round_number: number;
    timestamp?: string;
    is_internal?: boolean;
}

const MessageItem: React.FC<{ message: any }> = ({ message }) => {
    const isUser = message.agent_name === 'user';
    const isArbiter = message.agent_name.toLowerCase() === 'arbiter';

    const getAgentStyles = (name: string) => {
        const n = name.toLowerCase();
        if (n === 'user') return 'bg-white border-slate-200 shadow-sm self-end';
        if (n.includes('openai') || n.includes('llama')) return 'bg-white border-slate-200 border-l-4 border-l-slate-400 shadow-sm';
        if (n.includes('gemini') || n.includes('qwen')) return 'bg-white border-slate-200 border-l-4 border-l-sky-500 shadow-sm';
        if (n.includes('deepseek') || n.includes('phi')) return 'bg-white border-slate-200 border-l-4 border-l-indigo-500 shadow-sm';
        if (n.includes('arbiter')) return 'bg-amber-50 border-amber-200 border-l-4 border-l-amber-500 shadow-md ring-1 ring-amber-500/10';
        return 'bg-white border-slate-100 shadow-sm';
    };

    const getAgentIcon = (name: string) => {
        const n = name.toLowerCase();
        if (n === 'user') return '👤';
        if (n.includes('openai')) return '🤖';
        if (n.includes('llama')) return '🦙';
        if (n.includes('gemini')) return '✨';
        if (n.includes('qwen')) return '🧊';
        if (n.includes('deepseek')) return '🐳';
        if (n.includes('phi')) return 'Φ';
        if (n.includes('arbiter')) return '⚖️';
        return '🤖';
    };

    return (
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
            <div className={`max-w-[85%] md:max-w-[75%] rounded-2xl p-5 border ${getAgentStyles(message.agent_name)}`}>
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg bg-slate-50 w-8 h-8 flex items-center justify-center rounded-lg shadow-inner">
                        {getAgentIcon(message.agent_name)}
                    </span>
                    <span className={`text-xs font-black uppercase tracking-widest ${isArbiter ? 'text-amber-700' : 'text-slate-500'}`}>
                        {message.agent_name}
                        {message.round_number > 0 && <span className="ml-2 py-0.5 px-1.5 bg-slate-100 rounded text-[10px]">Round {message.round_number}</span>}
                    </span>
                </div>
                <div className={`text-sm leading-relaxed ${isArbiter ? 'text-slate-900 font-medium' : 'text-slate-700'}`}>
                    {message.content.split('\n').map((line: string, i: number) => (
                        <p key={i} className={line ? 'mb-2 last:mb-0' : 'h-2'} style={{ whiteSpace: 'pre-wrap' }}>
                            {line}
                        </p>
                    ))}
                </div>
            </div>
            {isUser && <div className="text-[10px] uppercase font-bold text-slate-400 mt-1 mr-2 tracking-tighter">You</div>}
        </div>
    );
};

export default MessageItem;
