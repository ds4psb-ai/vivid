"""
VDG v4.0 2-Pass Video Analysis Pipeline.

Components:
- SemanticPass: Pass 1 - Meaning, structure, intent analysis
- VisualPass: Pass 2 - Precision metrics and entity tracking
- AnalysisPlanner: Bridge between Pass 1 and Pass 2
- VDGMerger: Combines both passes with quality validation
- DirectorCompiler: Compiles VDG → DirectorPack for coaching

Usage:
    from app.services.vdg_2pass import SemanticPass, VisualPass, VDGMerger, DirectorCompiler
    
    # Run semantic analysis
    semantic = SemanticPass()
    result1 = await semantic.analyze(video_bytes, duration_sec, comments)
    
    # Generate analysis plan
    plan = AnalysisPlanner.plan(result1)
    
    # Run visual analysis
    visual = VisualPass()
    result2 = await visual.analyze(video_bytes, plan, result1.entity_hints, summary)
    
    # Merge results
    vdg = VDGMerger.merge(result1, result2, plan, content_id, video_url)
    
    # Compile to DirectorPack
    pack = DirectorCompiler.compile(vdg)

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from .semantic_pass import SemanticPass
from .visual_pass import VisualPass
from .analysis_planner import AnalysisPlanner
from .merger import VDGMerger
from .director_compiler import DirectorCompiler, compile_director_pack
from .frame_extractor import FrameExtractor, FrameEvidence
from .gemini_utils import robust_generate_content

__all__ = [
    "SemanticPass",
    "VisualPass",
    "AnalysisPlanner",
    "VDGMerger",
    "DirectorCompiler",
    "compile_director_pack",
    "FrameExtractor",
    "FrameEvidence",
    "robust_generate_content",
]
