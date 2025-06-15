// This file contains utility functions for chart generation
// Most chart logic is directly in the dashboard HTML files for simplicity

// Utility function to generate color scales
function generateColors(n) {
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', 
        '#FF9F40', '#8BC34A', '#03A9F4', '#F44336', '#9C27B0'
    ];
    
    if (n <= colors.length) {
        return colors.slice(0, n);
    }
    
    // Generate additional colors if needed
    const result = [...colors];
    for (let i = colors.length; i < n; i++) {
        const hue = (i * 137.5) % 360;
        result.push(`hsl(${hue}, 70%, 60%)`);
    }
    
    return result;
}

// Utility function to format data for various chart types
function formatDataForCharts(rawData, chartType) {
    switch (chartType) {
        case 'pie':
            return {
                labels: rawData.map(item => item.label),
                datasets: [{
                    data: rawData.map(item => item.value),
                    backgroundColor: generateColors(rawData.length),
                    borderWidth: 1
                }]
            };
            
        case 'bar':
            return {
                labels: rawData.map(item => item.label),
                datasets: [{
                    label: rawData.datasetLabel || 'Value',
                    data: rawData.map(item => item.value),
                    backgroundColor: generateColors(rawData.length),
                    borderWidth: 1
                }]
            };
            
        case 'line':
            return {
                labels: rawData.map(item => item.label),
                datasets: [{
                    label: rawData.datasetLabel || 'Value',
                    data: rawData.map(item => item.value),
                    fill: false,
                    borderColor: '#36A2EB',
                    tension: 0.4
                }]
            };
            
        case 'scatter':
            return {
                datasets: [{
                    label: rawData.datasetLabel || 'Value',
                    data: rawData.map(item => ({
                        x: item.x,
                        y: item.y
                    })),
                    backgroundColor: '#FF6384',
                    borderColor: '#FF6384',
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            };
            
        default:
            console.error('Unsupported chart type:', chartType);
            return {};
    }
}

// Function to calculate statistics for dataset analysis
function calculateStats(data) {
    if (!data || data.length === 0) return {};
    
    const sum = data.reduce((acc, val) => acc + val, 0);
    const mean = sum / data.length;
    
    // Sort for median and percentiles
    const sorted = [...data].sort((a, b) => a - b);
    const median = sorted.length % 2 === 0 
        ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
        : sorted[Math.floor(sorted.length / 2)];
    
    // Calculate standard deviation
    const squaredDiffs = data.map(val => Math.pow(val - mean, 2));
    const variance = squaredDiffs.reduce((acc, val) => acc + val, 0) / data.length;
    const stdDev = Math.sqrt(variance);
    
    return {
        count: data.length,
        min: sorted[0],
        max: sorted[sorted.length - 1],
        mean: mean,
        median: median,
        stdDev: stdDev
    };
}
