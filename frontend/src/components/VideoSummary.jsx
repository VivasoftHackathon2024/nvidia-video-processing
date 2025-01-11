import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const VideoSummary = ({ summaryResult, sx = {} }) => {
    if (!summaryResult || !summaryResult.summary) {
        return null;
    }

    return (
        <Paper
            elevation={3}
            sx={{
                p: 2,
                backgroundColor: '#f8f9fa',
                borderRadius: 2,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                ...sx // Allow custom styles to be passed in
            }}
        >
            <Typography
                variant="h5"
                gutterBottom
                sx={{
                    // color: '#1976d2',
                    fontWeight: 'bold'
                }}
            >
                Video Summary
            </Typography>

            <Box sx={{
                bgcolor: 'background.paper',
                boxShadow: 3,
                flex: 1,
                p: 5,
                overflow: 'auto',
                '&::-webkit-scrollbar': {
                    width: '6px',
                },
                '&::-webkit-scrollbar-track': {
                    background: '#f1f1f1',
                },
                '&::-webkit-scrollbar-thumb': {
                    background: '#888',
                    borderRadius: '3px',
                },
                '&::-webkit-scrollbar-thumb:hover': {
                    background: '#555',
                },
            }}>
                <Typography
                    variant="body1"
                    sx={{
                        whiteSpace: 'pre-wrap',
                        lineHeight: 1.6,
                        px: 1,
                        justifyContent: 'center',
                        display: 'flex',
                    }}
                >
                    {summaryResult.summary}
                </Typography>
            </Box>
        </Paper>
    );
};

export default VideoSummary;