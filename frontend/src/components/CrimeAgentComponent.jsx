import React from 'react';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import { Box, Typography, Card, CardContent, Chip, Stack } from '@mui/material';
import WatchLaterIcon from '@mui/icons-material/WatchLater';
import DescriptionIcon from '@mui/icons-material/Description';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Accordion, AccordionSummary, AccordionDetails } from '@mui/material';


const CrimeAgentComponent = ({ crimeEvaluation }) => {


    // crimeEvaluation = {
    //     "crime_incidents": [
    //         {
    //             "severity": "high",
    //             "description": "A large building engulfed in flames, with intense fire and thick smoke.",
    //             "time_interval": {
    //                 "start_time_seconds": 30,
    //                 "end_time_seconds": 60
    //             }
    //         },
    //         {
    //             "severity": "medium",
    //             "description": "A different building on fire during the daytime, flames visible through the windows.",
    //             "time_interval": {
    //                 "start_time_seconds": 0,
    //                 "end_time_seconds": 30
    //             }
    //         },
    //         {
    //             "severity": "medium",
    //             "description": "A street view of a building on fire, with flames and smoke visible.",
    //             "time_interval": {
    //                 "start_time_seconds": 0,
    //                 "end_time_seconds": 30
    //             }
    //         },
    //         {
    //             "severity": "high"
    //         }
    //     ]
    // }

    // const parsedData = crimeEvaluation;


    const parsedData = crimeEvaluation?.crime_evaluation ?
        JSON.parse(crimeEvaluation.crime_evaluation) : null;



    const getSeverityColor = (severity) => {
        switch (severity.toLowerCase()) {
            case 'high':
                return '#dc2626';
            case 'medium':
                return '#f59e0b';
            case 'low':
                return '#10b981';
            default:
                return '#6b7280';
        }
    };

    if (!parsedData) return null;

    const lastIndex = parsedData.crime_incidents.length - 1;
    const lastIncidentSeverity = parsedData.crime_incidents[lastIndex].severity;

    return (
        <Accordion sx={{
            boxShadow: 3, borderRadius: 12, mb: 2
        }}>
            <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls="fire-incident-content"
                id="fire-incident-header"
                sx={{ p: 2 }}
            >
                <Typography variant="h6" sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    fontWeight: 'bold'
                }}>
                    <LocalFireDepartmentIcon sx={{ color: '#dc2626' }} />
                    Crime Incident Analysis
                    <Chip
                        label={lastIncidentSeverity.toUpperCase()}
                        color={
                            lastIncidentSeverity === 'high' ? 'error' :
                                lastIncidentSeverity === 'medium' ? 'warning' :
                                    'default'
                        }
                        sx={{ ml: 2 }}
                    />
                </Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ border: 1 }}>

                <Stack spacing={2}>
                    {parsedData.crime_incidents.slice(0, lastIndex).map((incident, index) => (
                        <Card
                            key={index}
                            sx={{
                                bgcolor: 'background.paper',
                                boxShadow: 3
                            }}
                        >
                            <CardContent>
                                <Box sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'flex-start',
                                    mb: 2
                                }}>
                                    <Chip
                                        label={incident.severity.toUpperCase()}
                                        sx={{
                                            bgcolor: getSeverityColor(incident.severity),
                                            color: 'white',
                                            fontWeight: 'bold',
                                            px: 1
                                        }}
                                    />

                                    {incident.time_interval && (
                                        <Box sx={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: 1,
                                            color: 'text.secondary'
                                        }}>
                                            <WatchLaterIcon fontSize="small" />
                                            <Typography variant="body2">
                                                {incident.time_interval.start_time_seconds}s - {incident.time_interval.end_time_seconds}s
                                            </Typography>
                                        </Box>
                                    )}
                                </Box>

                                {incident.description && (
                                    <Box sx={{
                                        display: 'flex',
                                        alignItems: 'flex-start',
                                        gap: 1,
                                        mt: 2
                                    }}>
                                        <DescriptionIcon sx={{ color: 'text.secondary', mt: 0.5 }} fontSize="small" />
                                        <Typography variant="body1" color="text.primary">
                                            {incident.description}
                                        </Typography>
                                    </Box>
                                )}
                            </CardContent>
                        </Card>
                    ))}
                </Stack>
            </AccordionDetails>
        </Accordion >
    );
};

export default CrimeAgentComponent;