
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const startDeliberation = async (
    question: string,
    apiKeys: { openai: string; gemini: string; deepseek: string },
    maxRounds: number = 3
) => {
    const response = await axios.post(`${API_BASE_URL}/conversation/start/`, {
        question,
        api_keys: apiKeys,
        max_rounds: maxRounds
    });
    return response.data; // { conversation_id: string }
};

export const getConversationHistory = async (conversationId: string) => {
    const response = await axios.get(`${API_BASE_URL}/conversation/${conversationId}/history/`);
    return response.data; // Message[]
};

export const getStreamUrl = (conversationId: string) => {
    return `${API_BASE_URL}/conversation/${conversationId}/stream/`;
};
