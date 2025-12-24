module.exports = [
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[project]/src/lib/translations.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "translations",
    ()=>translations
]);
const translations = {
    ko: {
        // General
        appName: "비비드 노드 캔버스",
        loading: "로딩 중...",
        error: "오류 발생",
        save: "저장",
        cancel: "취소",
        delete: "삭제",
        close: "닫기",
        run: "실행",
        generate: "생성",
        generating: "생성 중...",
        running: "실행 중...",
        optimizing: "최적화 중...",
        version: "버전",
        // Header & Nav
        newProject: "새 프로젝트",
        openProject: "불러오기",
        untitledProject: "제목 없는 프로젝트",
        // Canvas Dock
        addNode: "노드 추가",
        nodeInput: "입력",
        nodeStyle: "스타일",
        nodeCustom: "커스텀",
        nodeProcess: "처리",
        nodeCapsule: "캡슐",
        nodeOutput: "출력",
        // Template Cards
        createCanvas: "캔버스 생성",
        versions: "버전",
        creating: "생성 중...",
        // Versions Modal
        templateVersions: "템플릿 버전",
        useVersion: "사용",
        revertVersion: "되돌리기",
        currentVersion: "현재",
        latestHistory: "최신 버전 기록",
        noVersions: "버전 기록이 없습니다.",
        loadingVersions: "버전 로딩 중...",
        // Inspector
        inspectorTitle: "속성",
        nodeId: "노드 ID",
        nodeType: "유형",
        nodeLabel: "이름",
        nodeSubtitle: "설명",
        params: "파라미터",
        capsuleParams: "캡슐 파라미터",
        nodeParams: "노드 파라미터",
        runCapsule: "캡슐 실행",
        runSummary: "실행 요약",
        runHistory: "실행 기록",
        noRuns: "실행 기록 없음",
        cachedResult: "캐시된 결과",
        evidenceRefs: "근거 자료",
        // Preview Panel
        storyboardPreview: "스토리보드 미리보기",
        styleVisualization: "스타일 시각화",
        colorPalette: "색상 팔레트",
        sceneBreakdown: "장면 분석",
        styleSignature: "스타일 시그니처",
        primary: "주색상",
        accent: "강조색",
        runId: "실행 ID",
        // Generation Panel
        generationResult: "생성 결과",
        beatSheet: "비트 시트",
        storyboard: "스토리보드",
        shot: "샷",
        beat: "비트",
        // Nodes
        generationPreview: "생성 미리보기",
        promptInput: "프롬프트 입력",
        userRequest: "사용자 요청",
        reasoningCore: "추론 코어",
        llmGa: "LLM + GA",
        finalResponse: "최종 응답",
        renderedOutput: "렌더링된 출력",
        // Additional Inspector
        sealedBadge: "봉인됨",
        lockedBadge: "잠김",
        sealedDesc: "봉인된 캡슐. 내부 체인이 숨겨져 있습니다.",
        lockedDesc: "템플릿 잠김. 노출된 파라미터만 수정 가능합니다.",
        deleteNode: "노드 삭제",
        generatedDesc: "생성된 스타일 시각화",
        durationHint: "길이 힌트",
        pacingNote: "페이스 노트",
        // Generation Panel Specific
        beatSheetStoryboardDesc: "비트 시트 및 스토리보드",
        noBeatSheet: "비트 시트가 아직 없습니다.",
        noStoryboard: "스토리보드가 아직 없습니다.",
        // Recommendations
        gaRecommendations: "GA 추천",
        topRecommendations: "상위 3개 최적화 파라미터 세트",
        recommendation: "추천",
        score: "점수",
        noSavedProjects: "저장된 프로젝트가 없습니다."
    },
    en: {
        // General
        appName: "Vivid Node Canvas",
        loading: "Loading...",
        error: "Error",
        save: "Save",
        cancel: "Cancel",
        delete: "Delete",
        close: "Close",
        run: "Run",
        generate: "Generate",
        generating: "Generating...",
        running: "Running...",
        optimizing: "Optimizing...",
        version: "Version",
        // Header & Nav
        newProject: "New Project",
        openProject: "Open Project",
        untitledProject: "Untitled Project",
        // Canvas Dock
        addNode: "Add Node",
        nodeInput: "Input",
        nodeStyle: "Style",
        nodeCustom: "Custom",
        nodeProcess: "Process",
        nodeCapsule: "Capsule",
        nodeOutput: "Output",
        // Template Cards
        createCanvas: "Create Canvas",
        versions: "Versions",
        creating: "Creating...",
        // Versions Modal
        templateVersions: "Template Versions",
        useVersion: "Use",
        revertVersion: "Revert",
        currentVersion: "Current",
        latestHistory: "Latest version history",
        noVersions: "No versions found.",
        loadingVersions: "Loading versions...",
        // Inspector
        inspectorTitle: "Inspector",
        nodeId: "Node ID",
        nodeType: "Type",
        nodeLabel: "Label",
        nodeSubtitle: "Subtitle",
        params: "Parameters",
        capsuleParams: "Capsule Parameters",
        nodeParams: "Node Parameters",
        runCapsule: "Run Capsule",
        runSummary: "Run Summary",
        runHistory: "Run History",
        noRuns: "No runs yet",
        cachedResult: "Cached Result",
        evidenceRefs: "Evidence Refs",
        // Preview Panel
        storyboardPreview: "Storyboard Preview",
        styleVisualization: "Style Visualization",
        colorPalette: "Color Palette",
        sceneBreakdown: "Scene Breakdown",
        styleSignature: "Style Signature",
        primary: "Primary",
        accent: "Accent",
        runId: "Run ID",
        // Generation Panel
        generationResult: "Generation Result",
        beatSheet: "Beat Sheet",
        storyboard: "Storyboard",
        shot: "Shot",
        beat: "Beat",
        // Nodes
        generationPreview: "Generation Preview",
        promptInput: "Prompt Input",
        userRequest: "User request",
        reasoningCore: "Reasoning Core",
        llmGa: "LLM + GA",
        finalResponse: "Final Response",
        renderedOutput: "Rendered Output",
        // Additional Inspector
        sealedBadge: "Sealed",
        lockedBadge: "Locked",
        sealedDesc: "Sealed capsule. Internal chain is hidden.",
        lockedDesc: "Template locked. Only exposed params are editable.",
        deleteNode: "Delete Node",
        generatedDesc: "Generated style visualization",
        durationHint: "Duration Hint",
        pacingNote: "Pacing Note",
        // Generation Panel Specific
        beatSheetStoryboardDesc: "Beat sheet & storyboard",
        noBeatSheet: "No beat sheet yet.",
        noStoryboard: "No storyboard yet.",
        // Recommendations
        gaRecommendations: "GA Recommendations",
        topRecommendations: "Top 3 optimized parameter sets",
        recommendation: "Recommendation",
        score: "Score",
        noSavedProjects: "No saved projects found."
    }
};
}),
"[project]/src/contexts/LanguageContext.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "LanguageProvider",
    ()=>LanguageProvider,
    "useLanguage",
    ()=>useLanguage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$translations$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/translations.ts [app-ssr] (ecmascript)");
"use client";
;
;
;
const LanguageContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["createContext"])(undefined);
function LanguageProvider({ children }) {
    const [language, setLanguage] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("ko");
    const t = (key)=>{
        return __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$translations$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["translations"][language][key] || key;
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(LanguageContext.Provider, {
        value: {
            language,
            setLanguage,
            t
        },
        children: children
    }, void 0, false, {
        fileName: "[project]/src/contexts/LanguageContext.tsx",
        lineNumber: 22,
        columnNumber: 9
    }, this);
}
function useLanguage() {
    const context = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useContext"])(LanguageContext);
    if (context === undefined) {
        throw new Error("useLanguage must be used within a LanguageProvider");
    }
    return context;
}
}),
"[project]/node_modules/next/dist/server/route-modules/app-page/module.compiled.js [app-ssr] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
;
else {
    if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
    ;
    else {
        if ("TURBOPACK compile-time truthy", 1) {
            if ("TURBOPACK compile-time truthy", 1) {
                module.exports = __turbopack_context__.r("[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)");
            } else //TURBOPACK unreachable
            ;
        } else //TURBOPACK unreachable
        ;
    }
} //# sourceMappingURL=module.compiled.js.map
}),
"[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

module.exports = __turbopack_context__.r("[project]/node_modules/next/dist/server/route-modules/app-page/module.compiled.js [app-ssr] (ecmascript)").vendored['react-ssr'].ReactJsxDevRuntime; //# sourceMappingURL=react-jsx-dev-runtime.js.map
}),
"[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

module.exports = __turbopack_context__.r("[project]/node_modules/next/dist/server/route-modules/app-page/module.compiled.js [app-ssr] (ecmascript)").vendored['react-ssr'].React; //# sourceMappingURL=react.js.map
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__7eec12f8._.js.map