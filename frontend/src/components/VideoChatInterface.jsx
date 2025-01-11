import React, { useState, useRef, useEffect } from 'react';
import {
    Box,
    Typography,
    IconButton,
    Avatar,
    Paper,
    InputBase,
    Divider,
    CircularProgress
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import SendIcon from '@mui/icons-material/Send';
import axios from 'axios';

const VideoChatInterface = ({ isOpen, onClose, threadId, videoId }) => {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: 'Hello! I can help you understand the video analysis results. What would you like to know?'
        }
    ]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const API_BASE_URL = import.meta.env.VITE_APP_BASE_URL;

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim() || !threadId) return;

        const userMessage = inputMessage.trim();
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setInputMessage('');
        setIsLoading(true);

        try {
            const response = await axios.post(
                `${API_BASE_URL}/videos/${videoId}/chat/`,
                {
                    thread_id: threadId,
                    message: userMessage
                }
            );

            console.log('Chat response:', response.data);

            // Only add messages from the assistant
            const newMessages = response.data.response
                .filter(msg => msg.role !== 'human' && msg.role !== 'tool' && msg.content.trim() !== '')  // Filter out user and tool messages
                .map(msg => ({
                    role: msg.role,
                    content: msg.content
                }));

            setMessages(prev => [...prev, ...newMessages]);
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box className={`chat-interface ${isOpen ? 'open' : ''}`}>
            <Box sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 2,
                borderBottom: '1px solid #e0e0e0',
                pb: 2,

            }}>
                <Typography variant="h6">Video Chat Assistant</Typography>
                <IconButton onClick={onClose}>
                    <CloseIcon />
                </IconButton>
            </Box>

            {/* Chat Messages */}
            <Box sx={{
                height: 'calc(100vh - 180px)',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                mb: 2
            }}>
                {messages.map((message, index) => (
                    <Box
                        key={index}
                        sx={{
                            display: 'flex',
                            gap: 1,
                            alignItems: 'flex-start',
                            flexDirection: message.role === 'user' ? 'row-reverse' : 'row'
                        }}
                    >
                        <Avatar sx={{
                            bgcolor: message.role === 'user' ? '#4caf50' : '#1976d2'
                        }}>
                            {message.role === 'user' ? 'U' : 'AI'}
                        </Avatar>
                        <Paper sx={{
                            p: 2,
                            maxWidth: '80%',
                            bgcolor: message.role === 'user' ? '#1976D2' : '#f5f5f5'
                        }}>
                            <Typography variant="body1"
                                sx={{
                                    color: message.role === 'user' ? '#fff' : '#000'
                                }}
                            >
                                {message.content}
                            </Typography>
                        </Paper>
                    </Box>
                ))}
                <div ref={messagesEndRef} />
                {isLoading && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                        <CircularProgress size={24} />
                    </Box>
                )}
            </Box>

            {/* Chat Input */}
            <Paper
                component="form"
                onSubmit={handleSendMessage}
                sx={{
                    p: '2px 4px',
                    display: 'flex',
                    alignItems: 'center',
                    position: 'absolute',
                    bottom: 20,
                    left: 20,
                    right: 20
                }}
            >
                <InputBase
                    sx={{ ml: 1, flex: 1 }}
                    placeholder="Type your message..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    disabled={isLoading}
                />
                <Divider sx={{ height: 28, m: 0.5 }} orientation="vertical" />
                <IconButton
                    color="primary"
                    sx={{ p: '10px' }}
                    type="submit"
                    disabled={isLoading || !inputMessage.trim()}
                >
                    <SendIcon />
                </IconButton>
            </Paper>
        </Box>
    );
};

export default VideoChatInterface;