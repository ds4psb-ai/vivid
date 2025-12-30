'use client';

import React from 'react';
import MetricsDashboard from '@/components/MetricsDashboard';

export default function MetricsPage() {
    return (
        <MetricsDashboard
            onRefresh={() => {
                console.log('Metrics refreshed');
            }}
        />
    );
}
