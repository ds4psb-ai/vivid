from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import os

KOREAN_FONT = "Apple SD Gothic Neo"
IMAGE_DIR = "/Users/ted/vivid/scripts/ppt_screenshots"

# 통합 슬라이드 데이터 (12장)
slides_data = [
    # Slide 1
    {
        "type": "cover",
        "title": "크레빗 x 넥스트러너스",
        "subtitle": "코딩 + 콘텐츠 = 전인적 사업가 양성",
        "desc": "2026.01.09 첫 미팅 자료"
    },
    # Slide 2
    {
        "type": "vision",
        "title": "공통 비전",
        "left_title": "넥스트러너스",
        "left_items": ["바이브코딩", "개발자가 AI 코드 검증", "결과물: 1인 SaaS/서비스", "제품을 만든다"],
        "right_title": "크레빗",
        "right_items": ["컨셉 디렉팅", "디렉터가 AI 영상 검증", "결과물: 브랜드 스토리, 마케팅 영상", "제품을 판다"],
        "bottom": "둘이 합치면 = 혼자서 만들고 팔 수 있는 1인 사업가"
    },
    # Slide 3
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
    # Slide 4
    {
        "type": "pipeline_overview",
        "title": "솔루션: 크레빗 파이프라인",
        "image": "flow-workflow.png",
        "desc": "4단계 워크플로우, 10개 차원 앱의 유기적 연결"
    },
    # Slide 5: Stage 1 (3 Apps)
    {
        "type": "apps_grid",
        "title": "1단계: 정체성 & 기획",
        "apps": [
            {"name": "심연의 거울", "img": "abyss-mirror.png", "desc": "창업자 DNA 분석"},
            {"name": "레퍼런스 해석기", "img": "reference-decoder.png", "desc": "스타일/연출 분석"},
            {"name": "시나리오 생성기", "img": "story-architect.png", "desc": "구조화된 스토리 변환"}
        ]
    },
    # Slide 6: Stage 2 (4 Apps)
    {
        "type": "apps_grid",
        "title": "2단계: 사전 제작 (설계)",
        "apps": [
            {"name": "미학 디렉터", "img": "aesthetic-director.png", "desc": "비주얼 스타일 정의"},
            {"name": "스토리보드", "img": "storyboard-sketch.png", "desc": "시각적 컷 설계"},
            {"name": "사운드 크래프터", "img": "sound-crafter.png", "desc": "BGM/효과음 설계"},
            {"name": "프롬프트 연금술", "img": "prompt-alchemy.png", "desc": "AI 언어 변환"}
        ]
    },
    # Slide 7: Stage 3 (2 Apps)
    {
        "type": "apps_grid",
        "title": "3단계: 제작 (구현)",
        "apps": [
            {"name": "비주얼 리얼라이저", "img": "visual-realizer.png", "desc": "고품질 키프레임 생성"},
            {"name": "비디오 메이커", "img": "video-maker.png", "desc": "영상 생성 & 모션 제어"}
        ]
    },
    # Slide 8: Stage 4 (1 App)
    {
        "type": "app_highlight",
        "title": "4단계: 완성 (품질)",
        "name": "퀄리티 디렉터",
        "img": "quality-director.png",
        "desc": "전문가 품질 검수 & 업스케일링",
        "tech": "Human-in-the-loop 검증 시스템"
    },
    # Slide 9: Dimension Merge (New)
    {
        "type": "full_image",
        "title": "차원 확장: 아이디어의 성장",
        "image": "flow-train-view.png",
        "desc": "단순한 아이디어가 각 차원을 거치며 구체적인 결과물로 성장합니다."
    },
    # Slide 10
    {
        "type": "funnel",
        "title": "협업 모델: 퍼널 전략",
        "steps": [
            ("온라인 (넥스트러너스)", "AI 콘텐츠 크리에이터 기초\n국비지원 / K-디지털\n월 100~300명"),
            ("선별", "쇼케이스 평가\n상위 10% 선발"),
            ("오프라인 (크레빗)", "AI 영상 마스터 클래스\n프리미엄 과정\n20명 정예")
        ]
    },
    # Slide 11
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
    # Slide 12
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

def add_image_safe(slide, img_name, left, top, width=None, height=None):
    img_path = os.path.join(IMAGE_DIR, img_name)
    if os.path.exists(img_path):
        try:
            if width and height:
                slide.shapes.add_picture(img_path, left, top, width=width, height=height)
            elif width:
                slide.shapes.add_picture(img_path, left, top, width=width)
            elif height:
                slide.shapes.add_picture(img_path, left, top, height=height)
            else:
                slide.shapes.add_picture(img_path, left, top)
        except Exception as e:
            print(f"Error adding image {img_name}: {e}")
            shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width or Inches(2), height or Inches(2))
            shape.text = f"Image Error: {img_name}"
    else:
        print(f"Image not found: {img_path}")
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width or Inches(2), height or Inches(2))
        shape.text = f"Missing: {img_name}"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

for item in slides_data:
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_background(slide)
    
    # Common Title (except cover)
    if item["type"] != "cover":
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.33), Inches(0.8))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(36), RGBColor(255, 255, 255), bold=True)

    if item["type"] == "cover":
        # ... (Cover Logic Same as Before)
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(12.33), Inches(1.5))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["title"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(60), RGBColor(168, 85, 247), bold=True)
        
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
        # ... (Vision Logic Same as Before)
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.8), Inches(5.5), Inches(4))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = item["left_title"]
        set_font(p.runs[0], KOREAN_FONT, Pt(28), RGBColor(168, 85, 247), bold=True)
        for line in item["left_items"]:
            p = tf.add_paragraph()
            p.text = "  " + line
            set_font(p.runs[0], KOREAN_FONT, Pt(20), RGBColor(200, 200, 200))

        txBox = slide.shapes.add_textbox(Inches(7), Inches(1.8), Inches(5.5), Inches(4))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = item["right_title"]
        set_font(p.runs[0], KOREAN_FONT, Pt(28), RGBColor(134, 239, 172), bold=True)
        for line in item["right_items"]:
            p = tf.add_paragraph()
            p.text = "  " + line
            set_font(p.runs[0], KOREAN_FONT, Pt(20), RGBColor(200, 200, 200))
            
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(6), Inches(12.33), Inches(1))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["bottom"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(24), RGBColor(255, 215, 0), bold=True)

    elif item["type"] == "problem":
        # ... (Problem Logic Same)
        txBox = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(5))
        tf = txBox.text_frame
        for i, line in enumerate(item["lines"]):
            if i == 0: p = tf.paragraphs[0]
            else: p = tf.add_paragraph()
            p.text = line
            p.alignment = PP_ALIGN.CENTER
            if line.startswith("우리의"): set_font(p.runs[0], KOREAN_FONT, Pt(28), RGBColor(134, 239, 172), bold=True)
            elif line: set_font(p.runs[0], KOREAN_FONT, Pt(28), RGBColor(200, 200, 200))
            p.space_after = Pt(20)

    elif item["type"] == "pipeline_overview":
        add_image_safe(slide, item["image"], Inches(1.5), Inches(1.5), width=Inches(10.33))
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(6.5), Inches(12.33), Inches(0.8))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["desc"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(24), RGBColor(200, 200, 200))

    elif item["type"] == "apps_grid":
        app_count = len(item["apps"])
        margin = 0.5
        total_width = 13.333 - (margin * 2)
        col_width = total_width / app_count
        for i, app in enumerate(item["apps"]):
            left = Inches(margin + (i * col_width) + 0.1)
            width = Inches(col_width - 0.2)
            add_image_safe(slide, app["img"], left, Inches(1.5), width=width)
            txBox = slide.shapes.add_textbox(left, Inches(5), width, Inches(0.8))
            p = txBox.text_frame.paragraphs[0]
            p.text = app["name"]
            p.alignment = PP_ALIGN.CENTER
            set_font(p.runs[0], KOREAN_FONT, Pt(20), RGBColor(168, 85, 247), bold=True)
            txBox = slide.shapes.add_textbox(left, Inches(5.8), width, Inches(1.5))
            tf = txBox.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = app["desc"]
            p.alignment = PP_ALIGN.CENTER
            set_font(p.runs[0], KOREAN_FONT, Pt(16), RGBColor(200, 200, 200))

    elif item["type"] == "app_highlight":
        add_image_safe(slide, item["img"], Inches(2), Inches(1.5), width=Inches(9.33))
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(6), Inches(12.33), Inches(1.5))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = f"{item['name']}: {item['desc']}"
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(24), RGBColor(234, 179, 8), bold=True)
        p = tf.add_paragraph()
        p.text = item["tech"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(18), RGBColor(200, 200, 200))

    elif item["type"] == "full_image":
        add_image_safe(slide, item["image"], Inches(1), Inches(1.5), width=Inches(11.33))
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(6.8), Inches(12.33), Inches(0.7))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["desc"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(20), RGBColor(200, 200, 200))

    elif item["type"] == "funnel":
        colors = [RGBColor(168, 85, 247), RGBColor(234, 179, 8), RGBColor(134, 239, 172)]
        bg_colors = [RGBColor(40, 40, 60), RGBColor(60, 50, 40), RGBColor(40, 60, 40)]
        
        # Center X
        cx = Inches(13.333 / 2)
        start_y = Inches(1.8)
        
        # Wider spacing and distinct sizes
        widths = [Inches(10), Inches(7.5), Inches(5)]
        heights = [Inches(1.6), Inches(1.6), Inches(1.6)]
        
        for i, (step_title, step_desc) in enumerate(item["steps"]):
            w = widths[i]
            h = heights[i]
            left = cx - (w / 2)
            # Gap between shapes
            top = start_y + (i * 1.8) 
            
            # Trapezoid Shape
            shape = slide.shapes.add_shape(MSO_SHAPE.TRAPEZOID, left, top, w, h)
            
            # Invert trapezoid for funnel effect (Top 2 inverted, bottom normal base)
            # Actually for a funnel stack, they should all be inverted except maybe bottom?
            # Let's make them all inverted to look like a funnel pointing down
            shape.rotation = 180
            
            shape.fill.solid()
            shape.fill.fore_color.rgb = bg_colors[i]
            shape.line.color.rgb = colors[i]
            shape.line.width = Pt(2)
            
            # Text inside shape - Need to correct rotation for text
            # Since shape is rotated 180, text will be upside down.
            # We must add a separate text box on top of the shape, or un-rotate text.
            # Easier: Add independent text box CENTERED on the shape.
            
            # Remove default text frame from shape (or just ignore it)
            
            # Add Overlay Text Box
            text_top = top + Inches(0.1) # slight padding from top edge (which is visually bottom if rotated... wait)
            # If shape is rotated 180, top-left becomes bottom-right visually?
            # No, rotation is around center.
            # Let's just place a transparent textbox over the shape coordinates.
            
            txBox = slide.shapes.add_textbox(left, top, w, h)
            tf = txBox.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = step_title
            p.alignment = PP_ALIGN.CENTER
            set_font(p.runs[0], KOREAN_FONT, Pt(24), colors[i], bold=True)
            
            p = tf.add_paragraph()
            p.text = step_desc
            p.alignment = PP_ALIGN.CENTER
            set_font(p.runs[0], KOREAN_FONT, Pt(16), RGBColor(220, 220, 220))

    elif item["type"] == "revenue":
        # ... (Revenue Logic Same)
        txBox = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(11), Inches(4))
        tf = txBox.text_frame
        for i, (label, value) in enumerate(item["items"]):
            if i > 0: p = tf.add_paragraph()
            else: p = tf.paragraphs[0]
            p.text = f"{label}: {value}"
            p.alignment = PP_ALIGN.CENTER
            set_font(p.runs[0], KOREAN_FONT, Pt(24), RGBColor(200, 200, 200))
            p.space_after = Pt(30)
            
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(12.33), Inches(1))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["bottom"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(20), RGBColor(255, 215, 0))

    elif item["type"] == "next_steps":
        # ... (Next Steps Logic Same)
        txBox = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(11), Inches(3))
        tf = txBox.text_frame
        for i, step in enumerate(item["items"]):
            if i > 0: p = tf.add_paragraph()
            else: p = tf.paragraphs[0]
            p.text = f"{i+1}. {step}"
            set_font(p.runs[0], KOREAN_FONT, Pt(22), RGBColor(200, 200, 200))
            p.space_after = Pt(20)
            
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(5), Inches(12.33), Inches(2))
        p = txBox.text_frame.paragraphs[0]
        p.text = item["closing"]
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], KOREAN_FONT, Pt(24), RGBColor(168, 85, 247), bold=True)

output_path = "/Users/ted/Desktop/넥스트러너스_미팅_통합_비주얼.pptx"
prs.save(output_path)
print(f"완료: {output_path}")
