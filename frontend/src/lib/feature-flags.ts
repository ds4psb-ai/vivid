/**
 * Feature Flags
 *
 * Centralized feature flag management for controlling feature availability.
 * Use environment variables to enable/disable features.
 */

/**
 * Flow (Dimension Workflow) feature flag
 * - Controls visibility of Flow UI across the app
 * - Default: false (disabled)
 * - Set NEXT_PUBLIC_FLOW_ENABLED=true to enable
 */
export const FLOW_ENABLED = process.env.NEXT_PUBLIC_FLOW_ENABLED === "true";

/**
 * B2B API Credits (Wallet) feature flag
 * - Controls visibility of B2B wallet endpoints
 * - Default: false (disabled)
 * - Set NEXT_PUBLIC_B2B_WALLET_ENABLED=true to enable
 *
 * NOTE: B2B API credits/wallet is planned but not implemented.
 * No endpoints exist yet - this flag is for future use.
 * See: 13_CREDITS_AND_BILLING_SPEC_V1.md:255
 */
export const B2B_WALLET_ENABLED = process.env.NEXT_PUBLIC_B2B_WALLET_ENABLED === "true";

/**
 * Artifact Preview feature flag for Flow/Teaching paths
 * - Controls artifact preview in non-legacy paths
 * - Default: false (disabled)
 * - Set NEXT_PUBLIC_ARTIFACT_PREVIEW_ENABLED=true to enable
 *
 * NOTE: Artifact types (storyboard, shot_list, data_table) are currently
 * only generated in legacy capsule paths. Flow/Teaching paths require
 * backend updates to generate artifact_type in responses.
 * See: 10_UI_DESIGN_GUIDE_2025-12.md:262
 */
export const ARTIFACT_PREVIEW_ENABLED = process.env.NEXT_PUBLIC_ARTIFACT_PREVIEW_ENABLED === "true";
