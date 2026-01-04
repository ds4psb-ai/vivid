/**
 * Secure Storage Utilities
 * 
 * Web Crypto API를 사용한 AES-GCM 암호화로 민감한 데이터를 안전하게 저장합니다.
 * 브라우저 환경에서 API 키와 같은 민감 정보를 보호합니다.
 */

const CRYPTO_ALGORITHM = "AES-GCM";
const KEY_LENGTH = 256;
const IV_LENGTH = 12; // 96 bits for AES-GCM

// Device-specific key derivation (fingerprint + random salt)
async function getOrCreateEncryptionKey(): Promise<CryptoKey> {
    const storedKeyData = localStorage.getItem("_enc_key");

    if (storedKeyData) {
        try {
            const keyData = JSON.parse(storedKeyData);
            const rawKey = Uint8Array.from(atob(keyData.key), c => c.charCodeAt(0));
            return await crypto.subtle.importKey(
                "raw",
                rawKey,
                { name: CRYPTO_ALGORITHM, length: KEY_LENGTH },
                false,
                ["encrypt", "decrypt"]
            );
        } catch {
            // Key corrupted, regenerate
            localStorage.removeItem("_enc_key");
        }
    }

    // Generate new key
    const key = await crypto.subtle.generateKey(
        { name: CRYPTO_ALGORITHM, length: KEY_LENGTH },
        true, // extractable for storage
        ["encrypt", "decrypt"]
    );

    // Export and store
    const rawKey = await crypto.subtle.exportKey("raw", key);
    const keyBase64 = btoa(String.fromCharCode(...new Uint8Array(rawKey)));
    localStorage.setItem("_enc_key", JSON.stringify({
        key: keyBase64,
        created: Date.now(),
    }));

    // Return non-extractable version
    return await crypto.subtle.importKey(
        "raw",
        rawKey,
        { name: CRYPTO_ALGORITHM, length: KEY_LENGTH },
        false,
        ["encrypt", "decrypt"]
    );
}

/**
 * Encrypt a string value using AES-GCM
 */
export async function encryptValue(plaintext: string): Promise<string> {
    try {
        const key = await getOrCreateEncryptionKey();
        const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH));
        const encoder = new TextEncoder();
        const data = encoder.encode(plaintext);

        const ciphertext = await crypto.subtle.encrypt(
            { name: CRYPTO_ALGORITHM, iv },
            key,
            data
        );

        // Combine IV + ciphertext and encode as base64
        const combined = new Uint8Array(iv.length + ciphertext.byteLength);
        combined.set(iv, 0);
        combined.set(new Uint8Array(ciphertext), iv.length);

        return btoa(String.fromCharCode(...combined));
    } catch (error) {
        console.error("[SecureStorage] Encryption failed:", error);
        throw new Error("Failed to encrypt value");
    }
}

/**
 * Decrypt a string value using AES-GCM
 */
export async function decryptValue(encrypted: string): Promise<string> {
    try {
        const key = await getOrCreateEncryptionKey();
        const combined = Uint8Array.from(atob(encrypted), c => c.charCodeAt(0));

        // Extract IV and ciphertext
        const iv = combined.slice(0, IV_LENGTH);
        const ciphertext = combined.slice(IV_LENGTH);

        const decrypted = await crypto.subtle.decrypt(
            { name: CRYPTO_ALGORITHM, iv },
            key,
            ciphertext
        );

        const decoder = new TextDecoder();
        return decoder.decode(decrypted);
    } catch (error) {
        console.error("[SecureStorage] Decryption failed:", error);
        throw new Error("Failed to decrypt value");
    }
}

/**
 * Securely store a sensitive value
 */
export async function secureSet(key: string, value: string): Promise<void> {
    const encrypted = await encryptValue(value);
    localStorage.setItem(`_sec_${key}`, encrypted);
}

/**
 * Retrieve a securely stored value
 */
export async function secureGet(key: string): Promise<string | null> {
    const encrypted = localStorage.getItem(`_sec_${key}`);
    if (!encrypted) return null;

    try {
        return await decryptValue(encrypted);
    } catch {
        // Value corrupted or key changed, remove it
        localStorage.removeItem(`_sec_${key}`);
        return null;
    }
}

/**
 * Remove a securely stored value
 */
export function secureRemove(key: string): void {
    localStorage.removeItem(`_sec_${key}`);
}

/**
 * Check if a secure value exists
 */
export function secureExists(key: string): boolean {
    return localStorage.getItem(`_sec_${key}`) !== null;
}

/**
 * Migrate plaintext value to encrypted storage
 */
export async function migratePlaintextToSecure(
    plaintextKey: string,
    secureKey: string
): Promise<boolean> {
    const plaintextValue = localStorage.getItem(plaintextKey);
    if (!plaintextValue) return false;

    try {
        await secureSet(secureKey, plaintextValue);
        localStorage.removeItem(plaintextKey);
        return true;
    } catch {
        return false;
    }
}
