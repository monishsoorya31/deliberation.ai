
import React, { useState } from 'react';

interface ApiKeyModalProps {
    onSave: (keys: { openai: string; gemini: string; deepseek: string }, rounds: number) => void;
}

const ApiKeyModal: React.FC<ApiKeyModalProps> = ({ onSave }) => {
    const [keys, setKeys] = useState({ openai: '', gemini: '', deepseek: '' });
    const [isLocal, setIsLocal] = useState(false);
    const [rounds, setRounds] = useState(3);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (isLocal) {
            onSave({ openai: '', gemini: '', deepseek: '' }, rounds);
        } else {
            onSave(keys, rounds);
        }
    };

    const isReady = isLocal || keys.gemini || keys.deepseek;

    return (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-md flex items-center justify-center p-4 z-50">
            <div className="bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl p-6 w-full max-w-md border border-white/20 transform transition-all max-h-[90vh] overflow-y-auto">
                <div className="text-center mb-6">
                    <h2 className="text-2xl font-extrabold text-slate-800 tracking-tight mb-1">Configure Agents</h2>
                    <p className="text-slate-500 text-xs">
                        Choose your preferred deliberation backend. <br />
                        <span className="font-semibold text-sky-600">Local mode requires Ollama service.</span>
                    </p>
                </div>

                <div className="mb-6 p-1 bg-slate-100 rounded-2xl flex relative h-11">
                    <button
                        onClick={() => setIsLocal(false)}
                        className={`flex-1 flex items-center justify-center text-xs font-bold z-10 transition-colors ${!isLocal ? 'text-slate-800' : 'text-slate-500'}`}
                    >
                        API Cloud
                    </button>
                    <button
                        onClick={() => setIsLocal(true)}
                        className={`flex-1 flex items-center justify-center text-xs font-bold z-10 transition-colors ${isLocal ? 'text-slate-800' : 'text-slate-500'}`}
                    >
                        Ollama Local
                    </button>
                    <div
                        className={`absolute top-1 bottom-1 w-[calc(50%-4px)] bg-white rounded-xl shadow-sm transition-transform duration-300 ease-out ${isLocal ? 'translate-x-[calc(100%+4px)]' : 'translate-x-1'}`}
                    />
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    {!isLocal ? (
                        <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                            <div className="group">
                                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 px-1">OpenAI API Key (Optional)</label>
                                <input
                                    type="password"
                                    className="w-full bg-slate-50 border-0 ring-1 ring-slate-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-sky-500 transition-all outline-none text-sm"
                                    value={keys.openai}
                                    onChange={(e) => setKeys({ ...keys, openai: e.target.value })}
                                    placeholder="gpt-4o"
                                />
                            </div>

                            <div className="group">
                                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 px-1">Google Gemini API Key</label>
                                <input
                                    type="password"
                                    className="w-full bg-slate-50 border-0 ring-1 ring-slate-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-sky-500 transition-all outline-none text-sm"
                                    value={keys.gemini}
                                    onChange={(e) => setKeys({ ...keys, gemini: e.target.value })}
                                    placeholder="gemini-2.0-flash"
                                />
                            </div>

                            <div className="group">
                                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 px-1">DeepSeek API Key</label>
                                <input
                                    type="password"
                                    className="w-full bg-slate-50 border-0 ring-1 ring-slate-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-sky-500 transition-all outline-none text-sm"
                                    value={keys.deepseek}
                                    onChange={(e) => setKeys({ ...keys, deepseek: e.target.value })}
                                    placeholder="deepseek-chat"
                                />
                            </div>
                        </div>
                    ) : (
                        <div className="py-8 text-center space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <div className="w-16 h-16 bg-sky-100 rounded-2xl flex items-center justify-center mx-auto text-3xl">
                                🏠
                            </div>
                            <div>
                                <h3 className="font-bold text-slate-800">Local Mode Active</h3>
                                <p className="text-sm text-slate-500 px-8">Ensure Ollama is running on your Mac with <b>llama3.2:1b</b>, <b>qwen2.5:1.5b</b>, and <b>phi3:mini</b> pulled.</p>
                            </div>
                        </div>
                    )}

                    <div className="pt-2">
                        <div className="flex justify-between items-center mb-4 px-1">
                            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Deliberation Depth</label>
                            <span className="text-[10px] font-black text-sky-600 bg-sky-50 px-2 py-0.5 rounded-lg font-mono">{rounds} Rounds</span>
                        </div>
                        <input
                            type="range"
                            min="1"
                            max="5"
                            step="1"
                            value={rounds}
                            onChange={(e) => setRounds(parseInt(e.target.value))}
                            className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-sky-600"
                        />
                        <div className="flex justify-between text-[9px] text-slate-400 mt-1.5 font-bold px-1 italic">
                            <span>FAST</span>
                            <span>DEEP</span>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={!isReady}
                        className="w-full bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-xl py-3.5 hover:from-sky-700 hover:to-indigo-700 font-bold text-base shadow-lg hover:shadow-sky-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed group active:scale-[0.98] mt-2"
                    >
                        {isLocal ? 'Start Local Deliberation' : 'Initialize Cloud Agents'}
                        <span className="ml-2 transition-transform group-hover:translate-x-1 inline-block">→</span>
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ApiKeyModal;
