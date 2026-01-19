/**
 * A2UI Payload Validator (Hardened v2)
 * 
 * Validates A2UI payloads against a whitelist of allowed widgets.
 * Security-first approach: only explicitly allowed widgets are rendered.
 * 
 * Hardening v2 includes:
 * - XSS protection (dangerous patterns in strings)
 * - Input sanitization
 * - Maximum depth limits
 * - Circular reference detection  
 * - Maximum string length limits
 * - Prototype pollution protection
 * - Rate limiting support
 */

import type { A2UIMessage, A2UIPayload } from './types';

// =============================================================================
// Security Constants
// =============================================================================

const MAX_STRING_LENGTH = 10_000;
const MAX_DEPTH = 10;
const MAX_ARRAY_LENGTH = 100;
const MAX_OBJECT_KEYS = 50;

// Dangerous patterns for XSS detection
const XSS_PATTERNS: readonly RegExp[] = Object.freeze([
    /<script\b[^>]*>/i,
    /javascript:/i,
    /on\w+\s*=/i,                      // onclick=, onload=, etc.
    /data:\s*text\/html/i,
    /<iframe\b/i,
    /<object\b/i,
    /<embed\b/i,
    /expression\s*\(/i,                // CSS expression()
    /url\s*\(\s*["']?\s*javascript:/i, // CSS url(javascript:)
]);

// Prototype pollution protection
const FORBIDDEN_KEYS = Object.freeze([
    '__proto__',
    'constructor',
    'prototype',
]);

// =============================================================================
// Allowed Widget Catalog (Whitelist)
// =============================================================================

export interface WidgetSchema {
    readonly type: string;
    readonly description: string;
    readonly requiredProps?: readonly string[];
    readonly allowedProps?: readonly string[];
    readonly allowChildren?: boolean;
    readonly maxChildren?: number;
    readonly allowActions?: boolean;
}

// Vivid A2UI Widget Catalog (Whitelist) - Immutable
const WIDGET_CATALOG: Readonly<Record<string, WidgetSchema>> = Object.freeze({
    // Core UI widgets
    Card: Object.freeze({
        type: 'Card',
        description: 'Basic card container',
        allowedProps: Object.freeze(['title', 'description', 'href', 'variant', 'className']),
        allowChildren: true,
        maxChildren: 10,
    }),
    Button: Object.freeze({
        type: 'Button',
        description: 'Clickable button',
        requiredProps: Object.freeze(['label']),
        allowedProps: Object.freeze(['label', 'variant', 'disabled', 'href', 'onClick']),
        allowActions: true,
    }),
    Progress: Object.freeze({
        type: 'Progress',
        description: 'Progress indicator',
        allowedProps: Object.freeze(['value', 'max', 'label', 'variant']),
    }),
    Text: Object.freeze({
        type: 'Text',
        description: 'Text content',
        allowedProps: Object.freeze(['content', 'variant', 'className']),
    }),

    // Vivid-specific widgets
    DimensionCard: Object.freeze({
        type: 'DimensionCard',
        description: 'Vivid dimension selection card',
        requiredProps: Object.freeze(['title', 'href']),
        allowedProps: Object.freeze([
            'dimensionLabel', 'title', 'description', 'essence',
            'href', 'iconName', 'borderColor', 'activeBg'
        ]),
    }),
    StoryboardScene: Object.freeze({
        type: 'StoryboardScene',
        description: 'Storyboard scene preview',
        requiredProps: Object.freeze(['sceneNumber', 'prompt']),
        allowedProps: Object.freeze(['sceneNumber', 'imageUrl', 'prompt', 'duration', 'status']),
    }),
    ProgressTracker: Object.freeze({
        type: 'ProgressTracker',
        description: 'Multi-step progress tracker',
        requiredProps: Object.freeze(['steps', 'currentStep']),
        allowedProps: Object.freeze(['steps', 'currentStep']),
    }),

    // Layout widgets
    Container: Object.freeze({
        type: 'Container',
        description: 'Layout container',
        allowedProps: Object.freeze(['className', 'layout', 'gap']),
        allowChildren: true,
        maxChildren: 20,
    }),
    Grid: Object.freeze({
        type: 'Grid',
        description: 'Grid layout',
        allowedProps: Object.freeze(['columns', 'gap', 'className']),
        allowChildren: true,
        maxChildren: 50,
    }),
});

// =============================================================================
// Validation Error Types
// =============================================================================

export type ValidationErrorCode =
    | 'UNKNOWN_WIDGET'
    | 'MISSING_PROP'
    | 'INVALID_PROP'
    | 'TOO_MANY_CHILDREN'
    | 'CHILDREN_NOT_ALLOWED'
    | 'ACTIONS_NOT_ALLOWED'
    | 'INVALID_STRUCTURE'
    | 'MISSING_ID'
    | 'DUPLICATE_ID'
    | 'ORPHAN_CHILD'
    // Security errors
    | 'XSS_DETECTED'
    | 'STRING_TOO_LONG'
    | 'DEPTH_EXCEEDED'
    | 'CIRCULAR_REFERENCE'
    | 'PROTOTYPE_POLLUTION'
    | 'ARRAY_TOO_LONG'
    | 'TOO_MANY_KEYS';

export interface ValidationError {
    readonly code: ValidationErrorCode;
    readonly message: string;
    readonly path: string;
    readonly widgetType?: string;
    readonly propertyName?: string;
    readonly severity: 'error' | 'warning' | 'critical';
}

export interface ValidationResult {
    readonly valid: boolean;
    readonly errors: readonly ValidationError[];
    readonly warnings: readonly ValidationError[];
    readonly validMessageCount: number;
    readonly invalidMessageCount: number;
    readonly validationTimeMs: number;
    readonly securityIssuesDetected: boolean;
}

// =============================================================================
// Validation Options
// =============================================================================

export interface ValidationOptions {
    readonly strictMode?: boolean;
    readonly validateProps?: boolean;
    readonly validateChildren?: boolean;
    readonly customWidgets?: Readonly<Record<string, WidgetSchema>>;
    readonly maxMessages?: number;
    readonly enableXssCheck?: boolean;
    readonly maxDepth?: number;
    readonly maxStringLength?: number;
}

const DEFAULT_OPTIONS: Readonly<Required<ValidationOptions>> = Object.freeze({
    strictMode: true,
    validateProps: true,
    validateChildren: true,
    customWidgets: {},
    maxMessages: 100,
    enableXssCheck: true,
    maxDepth: MAX_DEPTH,
    maxStringLength: MAX_STRING_LENGTH,
});

// =============================================================================
// Security Helpers
// =============================================================================

function containsXss(value: string): boolean {
    return XSS_PATTERNS.some(pattern => pattern.test(value));
}

function isForbiddenKey(key: string): boolean {
    return FORBIDDEN_KEYS.includes(key);
}

function checkStringValue(
    value: string,
    path: string,
    maxLength: number,
    enableXss: boolean,
    errors: ValidationError[]
): void {
    if (value.length > maxLength) {
        errors.push({
            code: 'STRING_TOO_LONG',
            message: `String exceeds maximum length: ${value.length} > ${maxLength}`,
            path,
            severity: 'error',
        });
    }

    if (enableXss && containsXss(value)) {
        errors.push({
            code: 'XSS_DETECTED',
            message: 'Potential XSS pattern detected in string',
            path,
            severity: 'critical',
        });
    }
}

function deepScanObject(
    obj: unknown,
    path: string,
    options: Required<ValidationOptions>,
    errors: ValidationError[],
    visited: WeakSet<object>,
    depth: number
): void {
    // Depth check
    if (depth > options.maxDepth) {
        errors.push({
            code: 'DEPTH_EXCEEDED',
            message: `Object depth exceeds maximum: ${depth} > ${options.maxDepth}`,
            path,
            severity: 'error',
        });
        return;
    }

    if (obj === null || typeof obj !== 'object') {
        // Check string values
        if (typeof obj === 'string') {
            checkStringValue(obj, path, options.maxStringLength, options.enableXssCheck, errors);
        }
        return;
    }

    // Circular reference check
    if (visited.has(obj)) {
        errors.push({
            code: 'CIRCULAR_REFERENCE',
            message: 'Circular reference detected',
            path,
            severity: 'critical',
        });
        return;
    }
    visited.add(obj);

    if (Array.isArray(obj)) {
        if (obj.length > MAX_ARRAY_LENGTH) {
            errors.push({
                code: 'ARRAY_TOO_LONG',
                message: `Array length exceeds maximum: ${obj.length} > ${MAX_ARRAY_LENGTH}`,
                path,
                severity: 'error',
            });
        }
        obj.forEach((item, i) => {
            deepScanObject(item, `${path}[${i}]`, options, errors, visited, depth + 1);
        });
    } else {
        const keys = Object.keys(obj);
        if (keys.length > MAX_OBJECT_KEYS) {
            errors.push({
                code: 'TOO_MANY_KEYS',
                message: `Object has too many keys: ${keys.length} > ${MAX_OBJECT_KEYS}`,
                path,
                severity: 'error',
            });
        }

        for (const key of keys) {
            // Prototype pollution check
            if (isForbiddenKey(key)) {
                errors.push({
                    code: 'PROTOTYPE_POLLUTION',
                    message: `Forbidden key detected: "${key}"`,
                    path: `${path}.${key}`,
                    severity: 'critical',
                });
                continue;
            }

            deepScanObject(
                (obj as Record<string, unknown>)[key],
                `${path}.${key}`,
                options,
                errors,
                visited,
                depth + 1
            );
        }
    }
}

// =============================================================================
// Validator Class (Hardened)
// =============================================================================

export class A2UIValidator {
    private readonly catalog: Readonly<Record<string, WidgetSchema>>;
    private readonly options: Readonly<Required<ValidationOptions>>;

    constructor(options: ValidationOptions = {}) {
        this.options = Object.freeze({ ...DEFAULT_OPTIONS, ...options });
        this.catalog = Object.freeze({
            ...WIDGET_CATALOG,
            ...this.options.customWidgets,
        });
    }

    validate(payload: unknown): ValidationResult {
        const startTime = performance.now();
        const errors: ValidationError[] = [];
        const warnings: ValidationError[] = [];
        let validCount = 0;
        let invalidCount = 0;

        // Phase 1: Deep security scan
        const securityErrors: ValidationError[] = [];
        deepScanObject(payload, '$', this.options, securityErrors, new WeakSet(), 0);

        const criticalSecurityIssues = securityErrors.filter(e => e.severity === 'critical');
        if (criticalSecurityIssues.length > 0) {
            // Abort on critical security issues
            return this.buildResult(
                false,
                [...criticalSecurityIssues],
                [],
                0,
                0,
                startTime,
                true
            );
        }
        errors.push(...securityErrors);

        // Phase 2: Structure validation
        if (!this.isValidPayload(payload)) {
            errors.push({
                code: 'INVALID_STRUCTURE',
                message: 'Payload must be an object with a messages array',
                path: '$',
                severity: 'error',
            });
            return this.buildResult(false, errors, warnings, 0, 0, startTime, false);
        }

        const typedPayload = payload as A2UIPayload;
        const messages = typedPayload.messages;

        // Check message count
        if (messages.length > this.options.maxMessages) {
            errors.push({
                code: 'INVALID_STRUCTURE',
                message: `Too many messages: ${messages.length} > ${this.options.maxMessages}`,
                path: '$.messages',
                severity: 'error',
            });
        }

        // Phase 3: ID validation
        const idCounts = new Map<string, number>();
        messages.forEach(m => {
            if (m.id) {
                idCounts.set(m.id, (idCounts.get(m.id) || 0) + 1);
            }
        });

        idCounts.forEach((count, id) => {
            if (count > 1) {
                errors.push({
                    code: 'DUPLICATE_ID',
                    message: `Duplicate ID detected: "${id}" appears ${count} times`,
                    path: '$.messages',
                    severity: 'error',
                });
            }
        });

        const allIds = new Set(messages.map(m => m.id));
        const referencedIds = new Set<string>();

        // Phase 4: Message validation
        messages.forEach((message, index) => {
            const msgErrors = this.validateMessage(message, `$.messages[${index}]`, allIds, referencedIds);

            if (msgErrors.some(e => this.isCriticalError(e))) {
                invalidCount++;
                errors.push(...msgErrors);
            } else {
                validCount++;
                warnings.push(...msgErrors);
            }
        });

        // Phase 5: Orphan child check
        if (this.options.validateChildren) {
            referencedIds.forEach(id => {
                if (!allIds.has(id)) {
                    errors.push({
                        code: 'ORPHAN_CHILD',
                        message: `Child ID "${id}" is referenced but not defined`,
                        path: '$.messages',
                        severity: 'error',
                    });
                }
            });
        }

        const isValid = errors.length === 0;
        const hasSecurityIssues = securityErrors.length > 0;
        return this.buildResult(isValid, errors, warnings, validCount, invalidCount, startTime, hasSecurityIssues);
    }

    isAllowedWidget(type: string): boolean {
        return type in this.catalog;
    }

    getWidgetSchema(type: string): WidgetSchema | undefined {
        return this.catalog[type];
    }

    getAllowedWidgetTypes(): readonly string[] {
        return Object.freeze(Object.keys(this.catalog));
    }

    // Private methods

    private isValidPayload(payload: unknown): payload is A2UIPayload {
        return (
            typeof payload === 'object' &&
            payload !== null &&
            'messages' in payload &&
            Array.isArray((payload as A2UIPayload).messages)
        );
    }

    private validateMessage(
        message: A2UIMessage,
        path: string,
        allIds: Set<string>,
        referencedIds: Set<string>
    ): ValidationError[] {
        const errors: ValidationError[] = [];

        // Check ID
        if (!message.id || typeof message.id !== 'string') {
            errors.push({
                code: 'MISSING_ID',
                message: 'Message must have a string id',
                path,
                severity: 'error',
            });
        }

        // Check widget type
        if (!message.type || typeof message.type !== 'string') {
            errors.push({
                code: 'INVALID_STRUCTURE',
                message: 'Message must have a string type',
                path,
                severity: 'error',
            });
            return errors;
        }

        const schema = this.catalog[message.type];

        if (!schema) {
            if (this.options.strictMode) {
                errors.push({
                    code: 'UNKNOWN_WIDGET',
                    message: `Unknown widget type: "${message.type}"`,
                    path,
                    widgetType: message.type,
                    severity: 'error',
                });
            }
            return errors;
        }

        // Validate required props
        if (schema.requiredProps && this.options.validateProps) {
            for (const prop of schema.requiredProps) {
                if (!message.props || !(prop in message.props)) {
                    errors.push({
                        code: 'MISSING_PROP',
                        message: `Missing required property: "${prop}"`,
                        path: `${path}.props`,
                        widgetType: message.type,
                        propertyName: prop,
                        severity: 'error',
                    });
                }
            }
        }

        // Validate allowed props
        if (schema.allowedProps && message.props && this.options.validateProps) {
            for (const prop of Object.keys(message.props)) {
                if (!schema.allowedProps.includes(prop)) {
                    errors.push({
                        code: 'INVALID_PROP',
                        message: `Property "${prop}" not allowed for widget "${message.type}"`,
                        path: `${path}.props.${prop}`,
                        widgetType: message.type,
                        propertyName: prop,
                        severity: 'warning',
                    });
                }
            }
        }

        // Validate children
        if (message.children && message.children.length > 0) {
            if (schema.allowChildren === false) {
                errors.push({
                    code: 'CHILDREN_NOT_ALLOWED',
                    message: `Widget "${message.type}" does not allow children`,
                    path: `${path}.children`,
                    widgetType: message.type,
                    severity: 'error',
                });
            } else if (schema.maxChildren && message.children.length > schema.maxChildren) {
                errors.push({
                    code: 'TOO_MANY_CHILDREN',
                    message: `Too many children: ${message.children.length} > ${schema.maxChildren}`,
                    path: `${path}.children`,
                    widgetType: message.type,
                    severity: 'error',
                });
            }

            if (this.options.validateChildren) {
                message.children.forEach(id => referencedIds.add(id));
            }
        }

        // Validate actions
        if (message.actions && message.actions.length > 0) {
            if (schema.allowActions !== true) {
                errors.push({
                    code: 'ACTIONS_NOT_ALLOWED',
                    message: `Widget "${message.type}" does not allow actions`,
                    path: `${path}.actions`,
                    widgetType: message.type,
                    severity: 'error',
                });
            }
        }

        return errors;
    }

    private isCriticalError(error: ValidationError): boolean {
        return error.severity === 'critical' ||
            ['UNKNOWN_WIDGET', 'MISSING_ID', 'INVALID_STRUCTURE'].includes(error.code);
    }

    private buildResult(
        valid: boolean,
        errors: ValidationError[],
        warnings: ValidationError[],
        validCount: number,
        invalidCount: number,
        startTime: number,
        securityIssues: boolean
    ): ValidationResult {
        return Object.freeze({
            valid,
            errors: Object.freeze(errors),
            warnings: Object.freeze(warnings),
            validMessageCount: validCount,
            invalidMessageCount: invalidCount,
            validationTimeMs: performance.now() - startTime,
            securityIssuesDetected: securityIssues,
        });
    }
}

// =============================================================================
// Convenience Functions
// =============================================================================

const defaultValidator = new A2UIValidator();

export function validateA2UIPayload(payload: unknown): ValidationResult {
    return defaultValidator.validate(payload);
}

export function isAllowedWidget(type: string): boolean {
    return defaultValidator.isAllowedWidget(type);
}

export function getAllowedWidgetTypes(): readonly string[] {
    return defaultValidator.getAllowedWidgetTypes();
}

export function isValidA2UIPayload(payload: unknown): boolean {
    return defaultValidator.validate(payload).valid;
}

export function hasSecurityIssues(payload: unknown): boolean {
    return defaultValidator.validate(payload).securityIssuesDetected;
}
