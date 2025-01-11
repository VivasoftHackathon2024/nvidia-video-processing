import React, { useState } from 'react';
import {
    Button,
    TextField,
    Box,
    Typography,
    Snackbar,
    CircularProgress,
    IconButton,
} from '@mui/material';
import axios from 'axios';
import VideoAnalysisLogs from '../components/VideoAnalysisLogs';
import VideoSummary from '../components/VideoSummary';
import ChatIcon from '@mui/icons-material/Chat';
import CloseIcon from '@mui/icons-material/Close';
import VideoChatInterface from '../components/VideoChatInterface';
import FireAgentComponent from '../components/FireAgentComponent';
import AssaultAgentComponent from '../components/AssaultAgentComponent';
import CrimeAgentComponent from '../components/CrimeAgentComponent';
import DrugAgentComponent from '../components/DrugAgentComponent';
import TheftAgentComponent from '../components/TheftAgentComponent';

const VideoUpload = () => {

    const API_BASE_URL = import.meta.env.VITE_APP_BASE_URL;


    const [file, setFile] = useState(null);
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [notification, setNotification] = useState('');
    const [uploadedVideo, setUploadedVideo] = useState(null);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [threadId, setThreadId] = useState(null);
    const [chatError, setChatError] = useState('');
    const [fireEvaluation, setFireEvaluation] = useState(null);
    const [assaultEvaluation, setAssaultEvaluation] = useState(null);
    const [crimeEvaluation, setCrimeEvaluation] = useState(null);
    const [drugEvaluation, setDrugEvaluation] = useState(null);
    const [theftEvaluation, setTheftEvaluation] = useState(null);



    const initializeChat = async () => {
        try {
            const response = await axios.post(
                `${API_BASE_URL}/videos/${uploadedVideo.id}/initialize_chat_agent/`
            );

            if (response.data.thread_id) {
                setThreadId(response.data.thread_id);
                setIsChatOpen(true);
            }
        } catch (error) {
            console.error('Error initializing chat:', error);
            setChatError('Failed to initialize chat. Please try again.');
            setNotification('Failed to initialize chat. Please try again.');
        }
    };

    const handleChatClick = async () => {
        if (!threadId) {
            await initializeChat();
        } else {
            setIsChatOpen(true);
        }
    };

    const handleChatClose = () => {
        setIsChatOpen(false);
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        setLoading(true);

        const formData = new FormData();
        formData.append('video', file);
        formData.append('title', title);
        formData.append('description', description);

        try {
            const response = await axios.post(`${API_BASE_URL}/videos/`, formData);
            setUploadedVideo(response.data);
            setNotification('Video uploaded successfully!');
        } catch (error) {
            setNotification('Error uploading video');
        }
        setLoading(false);
    };

    const handleSummary = async () => {
        if (!uploadedVideo) return;

        setSummaryLoading(true);
        try {
            const response = await axios.post(
                `${API_BASE_URL}/videos/${uploadedVideo.id}/summarize_agent/`
            );
            setUploadedVideo(prevVideo => ({
                ...prevVideo,
                summary_result: response.data
            }));
            console.log('Summary generated:', response.data);
            setNotification('Summary generated successfully!');
            await handleFireAgent();
            await handleAssaultAgent();
            await handleCrimeAgent();
            await handleDrugAgent();
            await handleTheftAgent();
        } catch (error) {
            console.error('Summary generation error:', error);
            setNotification('Error generating summary');
        } finally {
            setSummaryLoading(false);
        }
    };

    const handleFireAgent = async () => {
        if (!uploadedVideo) return;

        try {
            const response = await axios.post(
                `${API_BASE_URL}/videos/${uploadedVideo.id}/fire_agent/`
            );
            setFireEvaluation(response.data);
            setNotification('Fire analysis complete!');
        } catch (error) {
            console.error('Fire analysis error:', error);
            setNotification('Error analyzing fire incidents');
        }
    };

    const handleAssaultAgent = async () => {
        if (!uploadedVideo) return;

        try {
            const response = await axios.post(
                `${API_BASE_URL}/videos/${uploadedVideo.id}/assault_agent/`
            );
            setAssaultEvaluation(response.data);
            setNotification('Assault analysis complete!');
        } catch (error) {
            console.error('Assault analysis error:', error);
            setNotification('Error analyzing assault incidents');
        }
    };

    const handleCrimeAgent = async () => {
        if (!uploadedVideo) return;

        try {
            const response = await axios.post(
                `${API_BASE_URL}/videos/${uploadedVideo.id}/crime_agent/`
            );
            setCrimeEvaluation(response.data);
            setNotification('Crime analysis complete!');
        } catch (error) {
            console.error('Crime analysis error:', error);
            setNotification('Error analyzing crime incidents');
        }
    };

    const handleDrugAgent = async () => {
        if (!uploadedVideo) return;

        try {
            const response = await axios.post(
                `${API_BASE_URL}/videos/${uploadedVideo.id}/drug_agent/`
            );
            setDrugEvaluation(response.data);
            setNotification('Drug analysis complete!');
        } catch (error) {
            console.error('Drug analysis error:', error);
            setNotification('Error analyzing drug incidents');
        }
    };

    const handleTheftAgent = async () => {
        if (!uploadedVideo) return;

        try {
            const response = await axios.post(
                `${API_BASE_URL}/videos/${uploadedVideo.id}/theft_agent/`
            );
            setTheftEvaluation(response.data);
            setNotification('Theft analysis complete!');
        } catch (error) {
            console.error('Theft analysis error:', error);
            setNotification('Error analyzing theft incidents');
        }
    };

    const handleAnalyze = async () => {
        if (!uploadedVideo) return;

        setLoading(true);
        try {
            const response = await axios.post(
                `${API_BASE_URL}/videos/${uploadedVideo.id}/analyze/`
            );
            setUploadedVideo({ ...uploadedVideo, analysis_result: response.data });
            setNotification('Analysis complete!');
            await handleSummary();
        } catch (error) {
            setNotification('Error analyzing video');
        }
        setLoading(false);
    };


    return (
        <>
            <Box
                className={`container-transition ${isChatOpen ? 'container-with-chat' : ''}`}
                sx={{
                    maxWidth: 1800,
                    margin: 'auto',
                    padding: 3,
                }}
            >


                <Box sx={{ maxWidth: 2000, margin: 'auto', padding: 3 }}>
                    <Typography variant="h4" gutterBottom>
                        Video Analyzer
                    </Typography>

                    <form onSubmit={handleUpload}>
                        <TextField
                            fullWidth
                            label="Title"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            margin="normal"
                        />

                        <TextField
                            fullWidth
                            label="Description"
                            multiline
                            rows={4}
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            margin="normal"
                        />

                        <div className='flex items-center justify-between m-0 p-0 border-b border-gray-300 pb-4 mb-4'>
                            <input
                                type="file"
                                accept="video/*"
                                onChange={(e) => setFile(e.target.files[0])}
                                style={{ margin: '20px 0' }}
                            />

                            <Button
                                variant="contained"
                                type="submit"
                                disabled={loading || !file}
                                sx={{ marginRight: 2 }}
                            >
                                Upload Video
                            </Button>
                        </div>


                        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                            {uploadedVideo && (
                                <Button
                                    variant="contained"
                                    onClick={handleAnalyze}
                                    disabled={loading}
                                >
                                    Analyze Video
                                </Button>
                            )}

                            {uploadedVideo?.analysis_result && (
                                <Button
                                    variant="contained"
                                    onClick={handleChatClick}
                                    startIcon={<ChatIcon />}
                                    disabled={loading}
                                >
                                    Chat
                                </Button>
                            )}
                        </Box>
                        {loading && <CircularProgress sx={{ marginLeft: 2 }} />}
                    </form>

                    {!uploadedVideo && (
                        <VideoAnalysisLogs />
                    )}

                    {uploadedVideo && (
                        <Box sx={{ marginTop: 4 }}>
                            <video
                                controls
                                width="100%"
                                src={uploadedVideo.video_url}
                            />

                            {/* Container for Analysis and Summary */}
                            <Box className="analysis-summary-container" sx={{
                                display: 'flex',
                                gap: 3,
                                mt: 3,
                                height: '700px', // Fixed height for both components
                                overflow: 'auto'
                            }}>
                                {/* Analysis Logs */}
                                <Box className="analysis-container" sx={{
                                    flex: 1,
                                    overflow: 'hidden' // Prevent container from growing


                                }}>
                                    {uploadedVideo.analysis_result && (
                                        <VideoAnalysisLogs
                                            analysisResult={uploadedVideo.analysis_result}
                                            sx={{
                                                height: '100%',
                                                overflow: 'auto'
                                            }}
                                        />
                                    )}
                                </Box>

                                {/* Summary */}
                                <Box sx={{
                                    flex: 1,
                                    overflow: 'auto' // Prevent container from growing
                                }}>
                                    {uploadedVideo.summary_result && (
                                        <VideoSummary
                                            summaryResult={uploadedVideo.summary_result}
                                            sx={{
                                                height: '100%',
                                                overflow: 'auto'
                                            }}
                                        />
                                    )}
                                </Box>
                            </Box>
                            <Box sx={{ mb: 4 }}>
                                <Box sx={{
                                    mb: 2,
                                    flex: 1,
                                    overflow: 'auto'
                                }}>
                                    <FireAgentComponent fireEvaluation={fireEvaluation} />
                                </Box>
                                <Box sx={{
                                    mb: 2,
                                    flex: 1,
                                    overflow: 'auto'
                                }}>
                                    <AssaultAgentComponent assaultEvaluation={assaultEvaluation} />
                                </Box>
                                <Box sx={{
                                    mb: 2,
                                    flex: 1,
                                    overflow: 'auto'
                                }}>
                                    <CrimeAgentComponent crimeEvaluation={crimeEvaluation} />
                                </Box>
                                <Box sx={{
                                    mb: 2,
                                    flex: 1,
                                    overflow: 'auto'
                                }}>
                                    <DrugAgentComponent drugEvaluation={drugEvaluation} />
                                </Box>
                                <Box sx={{
                                    mb: 2,
                                    flex: 1,
                                    overflow: 'auto'
                                }}>
                                    <TheftAgentComponent theftEvaluation={theftEvaluation} />
                                </Box>

                            </Box>


                        </Box>
                    )}



                    <Snackbar
                        open={!!notification}
                        autoHideDuration={6000}
                        onClose={() => setNotification('')}
                        message={notification}
                    />
                </Box>
                <VideoChatInterface
                    isOpen={isChatOpen}
                    onClose={handleChatClose}
                    threadId={threadId}
                    videoId={uploadedVideo?.id}
                />
                <Snackbar
                    open={!!chatError}
                    autoHideDuration={6000}
                    onClose={() => setChatError('')}
                    message={chatError}
                />
            </Box>
        </>

    );
};

export default VideoUpload;