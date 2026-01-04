/**
 * AG-UI Module
 * 
 * Provides AG-UI protocol compatibility layer for Vivid Studio.
 * This module maps existing SSE events to AG-UI standard events.
 */

export {
    AguiEventType,
    mapToAgui,
    isLifecycleEvent,
    isMessageEvent,
    isToolEvent,
    isStateEvent,
    isCustomEvent,
    hasValidationErrors,
    isMappedEvent,
    getOriginalSseType,
    isKnownSseType,
    getSupportedSseTypes,
    getAguiTypeForSse,
    type AguiEvent,
} from './eventMapper';
