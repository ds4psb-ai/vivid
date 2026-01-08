from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
import os

KOREAN_FONT = "Apple SD Gothic Neo"

# 통합 슬라이드 데이터 (10장)
slides_data = [
    # Part 1: 도입 (3장)
    {
        "type": "cover",
        "title": "크레빗 x 넥스트러너스",
        "subtitle": "코딩 + 콘텐츠 = 전인적 사업가 양성",
        "desc": "2026.01.09 첫 미팅 자료"
    },
    {
        "type": "vision",
        "title": "공통 비전",
        "left_title": "넥스트러너스",
        "left_items": ["바이브코딩", "개발자가 AI 코드 검증", "결과물: 1인 SaaS/서비스", "제품을 만든다"],
        "right_title": "크레빗",
        "right_items": ["컨셉 디렉팅", "디렉터가 AI 영상 검증", "결과물: 브랜드 스토리, 마케팅 영상", "제품을 판다"],
        "bottom": "둘이 합치면 = 혼자서 만들고 팔 수 있는 1인 사업가"
    },
    {
        "type": "problem",
        "title": "문제 제기",
        "lines": [
            "오즈코딩스쿨 졸업생이 서비스를 만들었다.",
            "그 서비스를 어떻게 팔까?",
            "마케팅 영상 없이는 보이지 않는다.",
            "",
            "우리의 제안:",
            "개발 교육에 콘텐츠 제작 모듈을 더한다."
        ]
    },
    
    # Part 2: 크레빗 소개 (4장)
    {
        "type": "section",
        "title": "크레빗 파이프라인",
        "desc": "4단계, 10개 앱"
    },
    {
        "type": "pipeline",
        "title": "4단계 워크플로우",
        "stages": [
            ("1단계: 기획", "심연의 거울, 레퍼런스 해석기, 시나리오 생성기"),
            ("2단계: 사전제작", "미학 디렉터, 스토리보드, 사운드, 프롬프트"),
            ("3단계: 제작", "비주얼 리얼라이저, 비디오 메이커"),
            ("4단계: 완성", "퀄리티 디렉터")
        ],
        "bottom": "AI가 90%를 해주면, 당신은 가장 중요한 10% 미학에 집중"
    },
    {
        "type": "app_combo",
        "title": "핵심 앱 1: 정체성 분석",
        "app1_name": "심연의 거울",
        "app1_desc": "창업자의 취향/DNA를 분석\nRAG 기반 페르소나 분석",
        "app2_name": "레퍼런스 해석기",
        "app2_desc": "좋은 영상을 보여주면 분석\n멀티모달 스타일 추출",
        "tech": "Google Gemini 3 Pro, NotebookLM (오즈코딩스쿨에서 가르치는 RAG와 같은 기술)"
    },
    {
        "type": "app_combo",
        "title": "핵심 앱 2: 제작",
        "app1_name": "시나리오 생성기",
        "app1_desc": "아이디어를 3막 구조 시나리오로 변환",
        "app2_name": "비디오 메이커",
        "app2_desc": "이미지를 영상으로 확장\nVeo, Kling, Runway",
        "tech": "Claude 4.5 Opus, Google Veo 3.1, Kling O1"
    },
    {
        "type": "app_single",
        "title": "핵심 앱 3: 품질",
        "app_name": "퀄리티 디렉터",
        "app_desc": "일관성, 동작 자연스러움, 노이즈 등 6가지 기준으로 검수\n혼자 만들어도 프로덕션급 품질 보장",
        "tech": "자동 품질 분석, 색보정 제안 시스템"
    },
    
    # Part 3: 협업 제안 (3장)
    {
        "type": "section",
        "title": "협업 제안",
        "desc": "퍼널 전략"
    },
    {
        "type": "funnel",
        "title": "협업 모델",
        "steps": [
            ("온라인 (넥스트러너스)", "AI 콘텐츠 크리에이터 기초\n국비지원 / K-디지털\n월 100~300명"),
            ("선별", "쇼케이스 평가\n상위 10% 선발"),
            ("오프라인 (크레빗)", "AI 영상 마스터 클래스\n프리미엄 과정\n20명 정예")
        ]
    },
    {
        "type": "revenue",
        "title": "수익 구조",
        "items": [
            ("온라인 기초", "넥스트러너스 100% (국비)"),
            ("오프라인 마스터", "7:3 쉐어"),
            ("플랫폼 구독", "크레빗 수익")
        ],
        "bottom": "모든 수강생이 크레빗 플랫폼 사용 = 사용자 확보"
    },
    {
        "type": "next_steps",
        "title": "다음 단계",
        "items": [
            "오즈코딩스쿨 졸업작품 영상화 모듈 설계",
            "K-디지털 트레이닝 신규 과정 검토",
            "크레빗 플랫폼 라이브 데모 일정 조율"
        ],
        "closing": "바이브코딩이 개발을 민주화했듯이,\n크레빗은 영상 제작을 민주화합니다."
    }
]

def set_font(run, font_name, size, color, bold=False):
    run.font.name = font_name
    run.font.size = size
    run.font.color.rgb = color
    run.font.bold = bold
    run._r.get_or_add_rPr().set(qn('w:eastAsia'), font_name)

def set_background(slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(10, 10, 10)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

for item in slides_data:
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_background(slide)
    
    if item["type"] == "cover":
        # Title
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(12.33), Inches(1.5))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(60), RGBColor(168, 85, 247), bold=True)
        
        # Subtitle
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(4.2), Inches(12.33), Inches(2))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = item["subtitle"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(28), RGBColor(226, 232, 240))
        
        p = tf.add_paragraph()
        p.text = item["desc"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(18), RGBColor(100, 100, 100))
    
    elif item["type"] == "vision":
        # Title
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(12.33), Inches(1))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(40), RGBColor(255, 255, 255), bold=True)
        
        # Left column
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.8), Inches(5.5), Inches(4))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = item["left_title"]
        set_font(p.runs[0], KOREAN_FONT, Pt(28), RGBColor(168, 85, 247), bold=True)
        for line in item["left_items"]:
            p = tf.add_paragraph()
            p.text = "  " + line
            set_font(p.runs[0], KOREAN_FONT, Pt(20), RGBColor(200, 200, 200))
        
        # Right column
        txBox = slide.shapes.add_textbox(Inches(7), Inches(1.8), Inches(5.5), Inches(4))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = item["right_title"]
        set_font(p.runs[0], KOREAN_FONT, Pt(28), RGBColor(134, 239, 172), bold=True)
        for line in item["right_items"]:
            p = tf.add_paragraph()
            p.text = "  " + line
            set_font(p.runs[0], KOREAN_FONT, Pt(20), RGBColor(200, 200, 200))
        
        # Bottom
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(6), Inches(12.33), Inches(1))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["bottom"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(24), RGBColor(255, 215, 0), bold=True)
    
    elif item["type"] == "problem":
        # Title
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(12.33), Inches(1))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(40), RGBColor(255, 255, 255), bold=True)
        
        # Lines
        txBox = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(5))
        tf = txBox.text_frame
        for i, line in enumerate(item["lines"]):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            p.text = line
            p.alignment = PP_ALIGN.CENTER
            if line.startswith("우리의"):
                set_font(p.runs[0], KOREAN_FONT, Pt(28), RGBColor(134, 239, 172), bold=True)
            elif line:
                set_font(p.runs[0], KOREAN_FONT, Pt(28), RGBColor(200, 200, 200))
            p.space_after = Pt(20)
    
    elif item["type"] == "section":
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(2.8), Inches(12.33), Inches(1.2))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(54), RGBColor(255, 255, 255), bold=True)
        
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(4.2), Inches(12.33), Inches(1))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["desc"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(32), RGBColor(196, 181, 253))
    
    elif item["type"] == "pipeline":
        # Title
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.33), Inches(0.8))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(36), RGBColor(255, 255, 255), bold=True)
        
        # Stages (4 columns)
        colors = [RGBColor(168, 85, 247), RGBColor(59, 130, 246), RGBColor(34, 197, 94), RGBColor(234, 179, 8)]
        for i, (stage_title, stage_apps) in enumerate(item["stages"]):
            left = Inches(0.5 + i * 3.2)
            txBox = slide.shapes.add_textbox(left, Inches(1.5), Inches(3), Inches(4))
            tf = txBox.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = stage_title
            set_font(p.runs[0], KOREAN_FONT, Pt(20), colors[i], bold=True)
            
            p = tf.add_paragraph()
            p.text = stage_apps
            set_font(p.runs[0], KOREAN_FONT, Pt(14), RGBColor(180, 180, 180))
        
        # Bottom
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(6), Inches(12.33), Inches(1))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["bottom"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(22), RGBColor(255, 215, 0))
    
    elif item["type"] == "app_combo":
        # Title
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.33), Inches(0.8))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        set_font(p.runs[0], KOREAN_FONT, Pt(32), RGBColor(192, 132, 252), bold=True)
        
        # App 1
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5.5), Inches(3))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = item["app1_name"]
        set_font(p.runs[0], KOREAN_FONT, Pt(24), RGBColor(168, 85, 247), bold=True)
        p = tf.add_paragraph()
        p.text = item["app1_desc"]
        set_font(p.runs[0], KOREAN_FONT, Pt(18), RGBColor(200, 200, 200))
        
        # App 2
        txBox = slide.shapes.add_textbox(Inches(7), Inches(1.5), Inches(5.5), Inches(3))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = item["app2_name"]
        set_font(p.runs[0], KOREAN_FONT, Pt(24), RGBColor(134, 239, 172), bold=True)
        p = tf.add_paragraph()
        p.text = item["app2_desc"]
        set_font(p.runs[0], KOREAN_FONT, Pt(18), RGBColor(200, 200, 200))
        
        # Tech
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(12.33), Inches(1.5))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = "[활용 기술]"
        set_font(p.runs[0], KOREAN_FONT, Pt(16), RGBColor(216, 180, 254), bold=True)
        p = tf.add_paragraph()
        p.text = item["tech"]
        set_font(p.runs[0], KOREAN_FONT, Pt(14), RGBColor(150, 150, 150))
    
    elif item["type"] == "app_single":
        # Title
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.33), Inches(0.8))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        set_font(p.runs[0], KOREAN_FONT, Pt(32), RGBColor(192, 132, 252), bold=True)
        
        # App
        txBox = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(3))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = item["app_name"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(28), RGBColor(234, 179, 8), bold=True)
        p = tf.add_paragraph()
        p.text = item["app_desc"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(20), RGBColor(200, 200, 200))
        
        # Tech
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(12.33), Inches(1.5))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = "[활용 기술]"
        set_font(p.runs[0], KOREAN_FONT, Pt(16), RGBColor(216, 180, 254), bold=True)
        p = tf.add_paragraph()
        p.text = item["tech"]
        set_font(p.runs[0], KOREAN_FONT, Pt(14), RGBColor(150, 150, 150))
    
    elif item["type"] == "funnel":
        # Title
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.33), Inches(0.8))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(36), RGBColor(255, 255, 255), bold=True)
        
        # Steps (3 columns with arrows)
        colors = [RGBColor(168, 85, 247), RGBColor(234, 179, 8), RGBColor(134, 239, 172)]
        for i, (step_title, step_desc) in enumerate(item["steps"]):
            left = Inches(0.5 + i * 4.2)
            txBox = slide.shapes.add_textbox(left, Inches(2), Inches(3.8), Inches(4))
            tf = txBox.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = step_title
            p.alignment = PP_ALIGN.CENTER
            set_font(p.runs[0], KOREAN_FONT, Pt(22), colors[i], bold=True)
            
            p = tf.add_paragraph()
            p.text = step_desc
            p.alignment = PP_ALIGN.CENTER
            set_font(p.runs[0], KOREAN_FONT, Pt(16), RGBColor(200, 200, 200))
    
    elif item["type"] == "revenue":
        # Title
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.33), Inches(0.8))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(36), RGBColor(255, 255, 255), bold=True)
        
        # Items
        txBox = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(11), Inches(4))
        tf = txBox.text_frame
        for i, (label, value) in enumerate(item["items"]):
            if i > 0:
                p = tf.add_paragraph()
            else:
                p = tf.paragraphs[0]
            p.text = f"{label}: {value}"
            p.alignment = PP_ALIGN.CENTER
            set_font(p.runs[0], KOREAN_FONT, Pt(24), RGBColor(200, 200, 200))
            p.space_after = Pt(30)
        
        # Bottom
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(12.33), Inches(1))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["bottom"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(20), RGBColor(255, 215, 0))
    
    elif item["type"] == "next_steps":
        # Title
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.33), Inches(0.8))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(36), RGBColor(255, 255, 255), bold=True)
        
        # Items
        txBox = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(11), Inches(3))
        tf = txBox.text_frame
        for i, step in enumerate(item["items"]):
            if i > 0:
                p = tf.add_paragraph()
            else:
                p = tf.paragraphs[0]
            p.text = f"{i+1}. {step}"
            set_font(p.runs[0], KOREAN_FONT, Pt(22), RGBColor(200, 200, 200))
            p.space_after = Pt(20)
        
        # Closing
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(5), Inches(12.33), Inches(2))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["closing"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(24), RGBColor(168, 85, 247), bold=True)

# Save
output_path = "/Users/ted/Desktop/넥스트러너스_미팅_통합.pptx"
prs.save(output_path)
print(f"완료: {output_path}")
print(f"총 슬라이드: {len(prs.slides)}장")
