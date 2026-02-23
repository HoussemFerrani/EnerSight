import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Custom hook for WebSocket connection to receive live energy data
 * 
 * @param {string} url - WebSocket URL (e.g., 'ws://localhost:8000/api/v1/ws/energy/live')
 * @param {object} options - Configuration options
 * @returns {object} - { data, isConnected, error, reconnect }
 */
export function useWebSocket(url, options = {}) {
    const {
        autoConnect = true,
        reconnectInterval = 5000,
        reconnectAttempts = 5,
        onMessage = null,
        onConnect = null,
        onDisconnect = null,
        onError = null,
    } = options;

    const [data, setData] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState(null);

    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectCountRef = useRef(0);
    const shouldReconnectRef = useRef(autoConnect);

    const connect = useCallback(() => {
        if (!url) return;

        try {
            // Close existing connection
            if (wsRef.current) {
                wsRef.current.close();
            }

            console.log('🔌 Connecting to WebSocket:', url);
            const ws = new WebSocket(url);

            ws.onopen = () => {
                console.log('✅ WebSocket connected');
                setIsConnected(true);
                setError(null);
                reconnectCountRef.current = 0;

                if (onConnect) {
                    onConnect();
                }
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    console.log('📨 Received:', message);

                    // Update state with new data
                    if (message.type === 'energy_reading' && message.data) {
                        setData(message.data);

                        if (onMessage) {
                            onMessage(message.data);
                        }
                    }
                } catch (err) {
                    console.error('Failed to parse WebSocket message:', err);
                }
            };

            ws.onerror = (event) => {
                console.error('❌ WebSocket error:', event);
                setError('WebSocket connection error');

                if (onError) {
                    onError(event);
                }
            };

            ws.onclose = (event) => {
                console.log('🔌 WebSocket disconnected:', event.code, event.reason);
                setIsConnected(false);
                wsRef.current = null;

                if (onDisconnect) {
                    onDisconnect(event);
                }

                // Attempt to reconnect
                if (shouldReconnectRef.current && reconnectCountRef.current < reconnectAttempts) {
                    reconnectCountRef.current += 1;
                    console.log(`🔄 Reconnecting... Attempt ${reconnectCountRef.current}/${reconnectAttempts}`);

                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, reconnectInterval);
                } else if (reconnectCountRef.current >= reconnectAttempts) {
                    console.error('❌ Max reconnection attempts reached');
                    setError('Connection lost. Please refresh the page.');
                }
            };

            wsRef.current = ws;
        } catch (err) {
            console.error('Failed to create WebSocket:', err);
            setError('Failed to connect to live data stream');
        }
    }, [url, reconnectInterval, reconnectAttempts, onConnect, onDisconnect, onError, onMessage]);

    const disconnect = useCallback(() => {
        shouldReconnectRef.current = false;

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }

        setIsConnected(false);
    }, []);

    const reconnect = useCallback(() => {
        reconnectCountRef.current = 0;
        shouldReconnectRef.current = true;
        connect();
    }, [connect]);

    // Auto-connect on mount
    useEffect(() => {
        if (autoConnect) {
            connect();
        }

        // Cleanup on unmount
        return () => {
            shouldReconnectRef.current = false;
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [autoConnect, connect]);

    return {
        data,
        isConnected,
        error,
        reconnect,
        disconnect,
    };
}

export default useWebSocket;
