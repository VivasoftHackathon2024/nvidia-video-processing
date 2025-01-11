import React, { useEffect, useState } from 'react';
import { Clock, ArrowRight } from 'lucide-react';
import { Box, Typography, Card, CardContent } from '@mui/material';

const VideoAnalysisLogs = ({ analysisResult = [] }) => {
  if (!analysisResult || analysisResult.length === 0) {
    return (
      <div className="mt-6">
        <p className="text-gray-600">
          No analysis results available yet.
        </p>
      </div>
    );
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="mt-4 space-y-4">
      <h2 className="text-2xl font-bold mb-2">
        Video Analysis Results
      </h2>


      <div className="p-2 drop-shadow-md border border-slate-200 max-h-[620px] overflow-y-auto pr-2 space-y-4 [&::-webkit-scrollbar]:w-[6px] [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-gray-100">
        {analysisResult.map((segment, index) => (
          <Card key={index} sx={{ boxShadow: 3, bgcolor: 'info.main', color: 'HighlightText', p: 2 }} className="hover:shadow-md transition-shadow">
            <CardContent sx={{ color: 'HighlightText' }} className="p-4">
              <div className="flex items-center gap-1 mb-2 ">
                <div className="flex items-center min-w-[120px]">
                  <Clock className="w-4 h-4" />
                  <span className="ml-2 font-medium w-12 inline-block">{formatTime(segment.start_time_seconds)}</span>
                  <ArrowRight className="w-4 h-4" />
                  <span className="ml-4 font-medium w-12 inline-block">{formatTime(segment.end_time_seconds)}</span>
                </div>
              </div>

              <hr className="my-2 border-gray-200" />

              <div className="mt-2 ">
                <p className="leading-relaxed ">
                  {segment.analysis?.choices?.[0]?.message?.content || 'No analysis available'}
                </p>
              </div>

              {index < analysisResult.length - 1 && (
                <div className="absolute left-1/2 transform -translate-x-1/2 mt-2">
                  <div className="w-px h-4 bg-gray-200"></div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default VideoAnalysisLogs;