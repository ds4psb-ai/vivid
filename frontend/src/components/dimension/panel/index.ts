/**
 * Panel Design Unity - Compound Component System
 *
 * Unified panel components for all 11 Dimension tools.
 *
 * @example
 * ```tsx
 * import { DimensionPanel } from '@/components/dimension/panel';
 *
 * export default function AestheticDirectorPanel() {
 *   return (
 *     <DimensionPanel dimensionCode="ad">
 *       <DimensionPanel.Header title="Aesthetic Director" creditCost={10} />
 *       <DimensionPanel.Sidebar>
 *         <DimensionPanel.Textarea label="Concept" />
 *         <DimensionPanel.GenerateButton>Generate</DimensionPanel.GenerateButton>
 *       </DimensionPanel.Sidebar>
 *       <DimensionPanel.Content>
 *         <DimensionPanel.Loading />
 *         <DimensionPanel.Error onRetry={handleRetry} />
 *         <DimensionPanel.Result>
 *           {result && <MyResultDisplay data={result} />}
 *         </DimensionPanel.Result>
 *       </DimensionPanel.Content>
 *     </DimensionPanel>
 *   );
 * }
 * ```
 *
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 */

// Main compound component
export { DimensionPanel } from "./DimensionPanel";

// Context and hooks
export {
  useDimensionPanel,
  useDimensionPanelOptional,
  DimensionPanelProvider,
} from "./DimensionPanelContext";

// Types
export type {
  DimensionPanelContextValue,
  DimensionPanelStyles,
  DimensionPanelProviderProps,
} from "./DimensionPanelContext";

export type { DimensionPanelProps } from "./DimensionPanel";
export type { HeaderProps } from "./Header";
export type { SidebarProps } from "./Sidebar";
export type { ContentProps } from "./Content";
export type { InputProps } from "./Input";
export type { TextareaProps } from "./Textarea";
export type { SelectProps, SelectOption } from "./Select";
export type { GenerateButtonProps } from "./GenerateButton";
export type { LoadingStateProps } from "./LoadingState";
export type { ErrorStateProps } from "./ErrorState";
export type { ResultCardProps } from "./ResultCard";
export type { EvidenceWrapperProps } from "./EvidenceWrapper";
export type { FeedbackWrapperProps } from "./FeedbackWrapper";
export type { NextNavWrapperProps } from "./NextNavWrapper";
export type { FileUploadWrapperProps } from "./FileUploadWrapper";

// Individual components (for advanced usage)
export { Header } from "./Header";
export { Sidebar } from "./Sidebar";
export { Content } from "./Content";
export { Input } from "./Input";
export { Textarea } from "./Textarea";
export { Select } from "./Select";
export { GenerateButton } from "./GenerateButton";
export { LoadingState } from "./LoadingState";
export { ErrorState } from "./ErrorState";
export { ResultCard } from "./ResultCard";
export { EvidenceWrapper } from "./EvidenceWrapper";
export { FeedbackWrapper } from "./FeedbackWrapper";
export { NextNavWrapper } from "./NextNavWrapper";
export { FileUploadWrapper } from "./FileUploadWrapper";
