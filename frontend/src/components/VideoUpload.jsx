import React, { useState } from 'react';
import {
    Button,
    TextField,
    Box,
    Typography,
    Snackbar,
    CircularProgress
} from '@mui/material';
import axios from 'axios';

const VideoUpload = () => {
    const [file, setFile] = useState(null);
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [notification, setNotification] = useState('');
    const [uploadedVideo, setUploadedVideo] = useState(null);

    const handleUpload = async (e) => {
        e.preventDefault();
        setLoading(true);

        const formData = new FormData();
        formData.append('video', file);
        formData.append('title', title);
        formData.append('description', description);

        try {
            const response = await axios.post('http://localhost:8000/api/videos/', formData);
            setUploadedVideo(response.data);
            setNotification('Video uploaded successfully!');
        } catch (error) {
            setNotification('Error uploading video');
        }
        setLoading(false);
    };

    const handleAnalyze = async () => {
        if (!uploadedVideo) return;

        setLoading(true);
        try {
            const response = await axios.post(
                `http://localhost:8000/api/videos/${uploadedVideo.id}/analyze/`
            );
            setUploadedVideo({ ...uploadedVideo, analysis_result: response.data });
            setNotification('Analysis complete!');
        } catch (error) {
            setNotification('Error analyzing video');
        }
        setLoading(false);
    };

    return (
        <Box sx={{ maxWidth: 600, margin: 'auto', padding: 3 }}>
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

                {uploadedVideo && (
                    <Button
                        variant="contained"
                        onClick={handleAnalyze}
                        disabled={loading}
                    >
                        Analyze Video
                    </Button>
                )}

                {loading && <CircularProgress sx={{ marginLeft: 2 }} />}
            </form>

            {uploadedVideo && (
                <Box sx={{ marginTop: 4 }}>
                    <video
                        controls
                        width="100%"
                        src={uploadedVideo.video_url}
                    />

                    {uploadedVideo.analysis_result && (
                        <Box sx={{ marginTop: 2 }}>
                            <Typography variant="h6">Analysis Result:</Typography>
                            <pre style={{ whiteSpace: 'pre-wrap' }}>
                                {JSON.stringify(uploadedVideo.analysis_result, null, 2)}
                            </pre>
                        </Box>
                    )}
                </Box>
            )}

            <Snackbar
                open={!!notification}
                autoHideDuration={6000}
                onClose={() => setNotification('')}
                message={notification}
            />
        </Box>
    );
};

export default VideoUpload;