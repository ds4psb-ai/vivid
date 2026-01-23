/**
 * Credits API Types
 * 
 * Types for credit balance, transactions, and top-up operations.
 */

export interface CreditBalance {
    user_id: string;
    balance: number;
    subscription_credits: number;
    topup_credits: number;
    promo_credits: number;
    promo_expires_at?: string | null;
}

export interface CreditTransaction {
    id: string;
    event_type: "topup" | "usage" | "reward" | "promo" | "refund";
    amount: number;
    balance_snapshot: number;
    description?: string | null;
    capsule_run_id?: string | null;
    meta?: Record<string, unknown>;
    created_at: string;
}

export interface CreditTransactionList {
    transactions: CreditTransaction[];
    total: number;
}

export interface TopupRequest {
    amount: number;
    pack_id?: string;
}

export interface TopupResponse {
    success: boolean;
    new_balance: number;
    transaction_id: string;
}
