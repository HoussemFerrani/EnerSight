import { useEffect, useState } from 'react';

/**
 * Mock live data generator - runs entirely in the browser
 * No backend needed! Perfect for demos and testing.
 */
export function useMockLiveData(options = {}) {
    const { updateInterval = 5000, autoStart = true } = options;

    const [data, setData] = useState(null);
    const [isActive, setIsActive] = useState(autoStart);

    useEffect(() => {
        if (!isActive) return;

        const generateReading = () => {
            const now = new Date();
            const hour = now.getHours();

            // Realistic daily pattern: higher during day (8am-8pm), lower at night
            const timeFactor = hour >= 8 && hour <= 20
                ? 1.0 + 0.3 * Math.sin((hour - 6) * Math.PI / 12)
                : 0.7;

            // Base consumption with pattern
            const baseConsumption = 150.0;
            const randomFactor = 0.85 + Math.random() * 0.3;
            let consumption = baseConsumption * timeFactor * randomFactor;

            // Occasional spikes (5% chance)
            if (Math.random() < 0.05) {
                consumption *= 1.5 + Math.random() * 0.5;
            }

            // Related metrics
            const voltage = 220 + Math.random() * 20;
            const current = consumption / voltage;
            const powerFactor = 0.85 + Math.random() * 0.1;
            const temperature = 18 + Math.random() * 10;
            const humidity = 40 + Math.random() * 30;
            const cost = consumption * 0.12;

            return {
                timestamp: now.toISOString(),
                consumption: parseFloat(consumption.toFixed(2)),
                voltage: parseFloat(voltage.toFixed(2)),
                current: parseFloat(current.toFixed(2)),
                power_factor: parseFloat(powerFactor.toFixed(2)),
                temperature: parseFloat(temperature.toFixed(1)),
                humidity: parseFloat(humidity.toFixed(1)),
                cost: parseFloat(cost.toFixed(2)),
                location: "Building A - Floor 1",
                device_id: "sensor_001",
                mode: "mock" // Indicates this is mock data
            };
        };

        // Generate initial reading immediately
        setData(generateReading());

        // Update every N seconds
        const interval = setInterval(() => {
            setData(generateReading());
            console.log('📊 Mock data updated (no backend needed)');
        }, updateInterval);

        return () => clearInterval(interval);
    }, [isActive, updateInterval]);

    return {
        data,
        isActive,
        start: () => setIsActive(true),
        stop: () => setIsActive(false),
    };
}

export default useMockLiveData;
