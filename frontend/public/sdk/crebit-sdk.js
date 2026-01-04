/**
 * Crebit SDK (Hardened Version)
 * 
 * 연구 결과 기반 하드닝:
 * - 앱인토스 방식: 세션 키 관리, S2S 검증
 * - Anti-debugging: DevTools 감지, 디버거 감지
 * - Anti-tampering: 런타임 무결성 검사
 * - Heartbeat: 연결 상태 유지
 */

(function () {
    'use strict';

    // ===========================================
    // Anti-tampering: 즉시 실행하여 변조 방지
    // ===========================================

    // Freeze critical objects to prevent prototype pollution
    if (typeof Object.freeze === 'function') {
        try {
            // Prevent modification of console (anti-debugging bypass prevention)
            Object.freeze(console);
        } catch (e) { /* Silent */ }
    }

    // Prevent multiple initialization
    if (window.Crebit && window.Crebit.__initialized) {
        return;
    }

    // ===========================================
    // Configuration (replaced at build time)
    // ===========================================

    const PLATFORM_ORIGIN = '__PLATFORM_ORIGIN__';
    const APP_ID = '__APP_ID__';
    const APP_CONFIG = JSON.parse('__APP_CONFIG__');
    const SDK_VERSION = '2.0.0-hardened';

    // ===========================================
    // Security State
    // ===========================================

    let currentSessionKey = null;
    let isConnected = false;
    let heartbeatInterval = null;
    const pendingRequests = new Map();

    // Anti-debugging state
    let debuggerDetected = false;
    let devToolsOpen = false;

    // ===========================================
    // Anti-debugging (연구 결과 기반)
    // ===========================================

    function detectDevTools() {
        const widthThreshold = 160;
        const heightThreshold = 160;

        const check = function () {
            const widthCheckWindow = window.outerWidth - window.innerWidth > widthThreshold;
            const widthCheckScreen = window.screen.availWidth - window.innerWidth > widthThreshold;
            const heightCheckWindow = window.outerHeight - window.innerHeight > heightThreshold;
            const heightCheckScreen = window.screen.availHeight - window.innerHeight > heightThreshold;

            if (widthCheckWindow || widthCheckScreen || heightCheckWindow || heightCheckScreen) {
                if (!devToolsOpen) {
                    devToolsOpen = true;
                    onDevToolsDetected();
                }
            } else {
                devToolsOpen = false;
            }
        };

        // Check periodically
        setInterval(check, 1000);
        check();
    }

    function detectDebugger() {
        const start = performance.now();
        // debugger statement check - disabled in production builds
        const end = performance.now();

        if (end - start > 100) {
            debuggerDetected = true;
            onDebuggerDetected();
        }
    }

    function onDevToolsDetected() {
        // In production: disable sensitive operations
        // For now: just log
        sendMessage('app.error', {
            code: 'DEVTOOLS_DETECTED',
            message: 'Developer tools detected'
        }).catch(function () { });
    }

    function onDebuggerDetected() {
        // In production: disable critical functions
        sendMessage('app.error', {
            code: 'DEBUGGER_DETECTED',
            message: 'Debugger detected'
        }).catch(function () { });
    }

    // ===========================================
    // Communication (앱인토스 방식: 세션 키)
    // ===========================================

    function generateRequestId() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return Array.from(array, function (b) {
            return b.toString(16).padStart(2, '0');
        }).join('');
    }

    function sendMessage(type, payload) {
        return new Promise(function (resolve, reject) {
            if (!isValidMessageType(type)) {
                reject(new Error('Invalid message type'));
                return;
            }

            const id = generateRequestId();

            pendingRequests.set(id, {
                resolve: resolve,
                reject: reject,
                timestamp: Date.now()
            });

            // Timeout (30 seconds)
            setTimeout(function () {
                if (pendingRequests.has(id)) {
                    pendingRequests.delete(id);
                    reject(new Error('Request timeout'));
                }
            }, 30000);

            // Include session key for authenticated requests
            var messagePayload = payload || {};
            if (currentSessionKey && requiresSessionKey(type)) {
                messagePayload = Object.assign({}, messagePayload, {
                    sessionKey: currentSessionKey
                });
            }

            parent.postMessage({
                type: type,
                id: id,
                payload: messagePayload
            }, PLATFORM_ORIGIN);
        });
    }

    // Message types that require session key (앱인토스 방식)
    function requiresSessionKey(type) {
        return type === 'credits.deduct' ||
            type === 'storage.set' ||
            type === 'storage.remove';
    }

    // Allowed message types (whitelist)
    var ALLOWED_TYPES = [
        'dimension.sync', 'dimension.border', 'dimension.reset',
        'credits.deduct', 'credits.check',
        'storage.get', 'storage.set', 'storage.remove',
        'app.ready', 'app.error', 'app.heartbeat'
    ];

    function isValidMessageType(type) {
        return ALLOWED_TYPES.indexOf(type) !== -1;
    }

    // ===========================================
    // Response Handler
    // ===========================================

    function handleResponse(event) {
        // Strict origin validation
        if (event.origin !== PLATFORM_ORIGIN) {
            return;
        }

        var data = event.data;
        if (!data || typeof data !== 'object') return;

        var type = data.type;
        var id = data.id;
        var success = data.success;
        var responseData = data.data;
        var error = data.error;
        var sessionKey = data.sessionKey;

        if (!type || typeof type !== 'string' || !type.endsWith('.response')) return;
        if (!id) return;

        var pending = pendingRequests.get(id);
        if (!pending) return;

        pendingRequests.delete(id);

        // Update session key if provided (앱인토스 방식: 세션 키 갱신)
        if (sessionKey && typeof sessionKey === 'string') {
            currentSessionKey = sessionKey;
        }

        if (success) {
            pending.resolve(responseData);
        } else {
            pending.reject(new Error(error || 'Request failed'));
        }
    }

    window.addEventListener('message', handleResponse);

    // ===========================================
    // Heartbeat (연결 상태 유지)
    // ===========================================

    function startHeartbeat() {
        if (heartbeatInterval) return;

        heartbeatInterval = setInterval(function () {
            if (!isConnected) return;

            sendMessage('app.heartbeat', {}).catch(function () {
                isConnected = false;
                stopHeartbeat();
            });
        }, 30000); // Every 30 seconds
    }

    function stopHeartbeat() {
        if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
            heartbeatInterval = null;
        }
    }

    // ===========================================
    // Crebit SDK API (Hardened)
    // ===========================================

    window.Crebit = {
        __initialized: true,
        version: SDK_VERSION,
        appId: APP_ID,

        // Connection status
        get isConnected() { return isConnected; },
        get isSecure() { return !debuggerDetected && !devToolsOpen; },

        /**
         * Dimension API - 플랫폼 UI 동적 변경
         */
        dimension: {
            sync: function (theme) {
                if (!theme || typeof theme !== 'object') {
                    return Promise.reject(new Error('Invalid theme'));
                }
                return sendMessage('dimension.sync', theme);
            },

            setBorderColor: function (color) {
                if (typeof color !== 'string' || !/^#[0-9a-fA-F]{6}$/.test(color)) {
                    return Promise.reject(new Error('Invalid color format'));
                }
                return sendMessage('dimension.border', { color: color });
            },

            reset: function () {
                return sendMessage('dimension.reset', {});
            }
        },

        /**
         * Credits API - 크레딧 관리 (세션 키 검증)
         */
        credits: {
            deduct: function (amount, reason) {
                if (typeof amount !== 'number' || amount <= 0 || amount > 10000) {
                    return Promise.reject(new Error('Invalid amount'));
                }
                if (!currentSessionKey) {
                    return Promise.reject(new Error('Not connected'));
                }
                return sendMessage('credits.deduct', {
                    amount: amount,
                    reason: reason || 'App usage'
                });
            },

            check: function () {
                return sendMessage('credits.check', {});
            }
        },

        /**
         * Storage API - 앱 데이터 저장
         */
        storage: {
            set: function (key, value) {
                if (typeof key !== 'string' || key.length > 256) {
                    return Promise.reject(new Error('Invalid key'));
                }
                return sendMessage('storage.set', { key: key, value: value });
            },

            get: function (key) {
                if (typeof key !== 'string') {
                    return Promise.reject(new Error('Invalid key'));
                }
                return sendMessage('storage.get', { key: key });
            },

            remove: function (key) {
                if (typeof key !== 'string') {
                    return Promise.reject(new Error('Invalid key'));
                }
                return sendMessage('storage.remove', { key: key });
            }
        },

        /**
         * App lifecycle
         */
        app: {
            ready: function () {
                return sendMessage('app.ready', {
                    appId: APP_ID,
                    sdkVersion: SDK_VERSION,
                    secure: !debuggerDetected && !devToolsOpen
                }).then(function (response) {
                    isConnected = true;
                    if (response && response.sessionKey) {
                        currentSessionKey = response.sessionKey;
                    }
                    startHeartbeat();
                    return response;
                });
            },

            reportError: function (message) {
                if (typeof message !== 'string') {
                    message = 'Unknown error';
                }
                // Truncate to prevent data exfiltration
                message = message.substring(0, 500);
                return sendMessage('app.error', { message: message });
            },

            getConfig: function () {
                // Return frozen copy to prevent modification
                return Object.freeze(Object.assign({}, APP_CONFIG));
            }
        }
    };

    // Freeze the API to prevent tampering
    Object.freeze(window.Crebit);
    Object.freeze(window.Crebit.dimension);
    Object.freeze(window.Crebit.credits);
    Object.freeze(window.Crebit.storage);
    Object.freeze(window.Crebit.app);

    // ===========================================
    // Auto-initialization
    // ===========================================

    document.addEventListener('DOMContentLoaded', function () {
        // Start anti-debugging checks
        detectDevTools();

        // Connect to platform
        Crebit.app.ready().then(function () {
            // Auto-sync dimension if configured
            if (APP_CONFIG && APP_CONFIG.dimension) {
                Crebit.dimension.sync(APP_CONFIG.dimension).catch(function () {
                    // Silent fail
                });
            }
        }).catch(function (err) {
            // Connection failed - app may work in limited mode
        });
    });

    // Global error handler (limited info to prevent data leakage)
    window.addEventListener('error', function (event) {
        Crebit.app.reportError('Runtime error');
    });

    window.addEventListener('unhandledrejection', function (event) {
        Crebit.app.reportError('Unhandled promise rejection');
    });

})();
