/**
 * NICE Payments (나이스페이) SDK utility
 * 
 * This module provides helper functions for integrating with NICE Payments
 * JS SDK for payment processing.
 */

// Extend Window interface for NICE SDK
declare global {
    interface Window {
        AUTHNICE?: {
            requestPay: (options: NicePaymentOptions) => void;
        };
    }
}

export interface NicePaymentOptions {
    clientId: string;
    method: 'card' | 'vbank' | 'bank' | 'cellphone' | 'kakao' | 'naverpay' | 'samsungpay';
    orderId: string;
    amount: number;
    goodsName: string;
    returnUrl: string;
    mallReserved?: string;
    buyerName?: string;
    buyerTel?: string;
    buyerEmail?: string;
    fnError?: (result: { errorCode: string; errorMsg: string }) => void;
}

export interface NiceCallbackData {
    authResultCode: string;
    authResultMsg: string;
    tid: string;
    clientId: string;
    orderId: string;
    amount: string;
    authToken?: string;
    signature?: string;
}

/**
 * Load NICE Payments JS SDK script
 */
export function loadNicePayScript(): Promise<void> {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (window.AUTHNICE) {
            resolve();
            return;
        }

        // Check if script tag already exists
        const existingScript = document.querySelector('script[src*="nicepay.co.kr"]');
        if (existingScript) {
            existingScript.addEventListener('load', () => resolve());
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://pay.nicepay.co.kr/v1/js/';
        script.async = true;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load NICE Pay SDK'));
        document.head.appendChild(script);
    });
}

/**
 * Request payment through NICE Payments
 */
export async function requestNicePayment(options: NicePaymentOptions): Promise<void> {
    await loadNicePayScript();

    if (!window.AUTHNICE) {
        throw new Error('NICE Pay SDK not loaded');
    }

    window.AUTHNICE.requestPay(options);
}

/**
 * Get NICE Payments client configuration from backend
 */
export async function getNicePayConfig(): Promise<{
    client_id: string;
    mode: string;
    js_sdk_url: string;
}> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
    const response = await fetch(`${API_BASE_URL}/api/v1/payment/config`);
    if (!response.ok) {
        throw new Error('Failed to fetch payment config');
    }
    return response.json();
}

/**
 * Generate a unique order ID
 */
export function generateOrderId(prefix: string = 'CREBIT'): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 8);
    return `${prefix}_${timestamp}_${random}`.toUpperCase();
}

/**
 * Crebit ATC payment constants
 */
export const CREBIT_PAYMENT = {
    AMOUNT: 340000,  // 34만원
    GOODS_NAME: 'Crebit ATC 1기 수강권',
    EARLY_BIRD_AMOUNT: 340000,
} as const;
