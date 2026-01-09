from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

# 기존 문서 열기
doc = Document('/Users/ted/Downloads/AI 영상 제작 클래스 커리큘럼.docx')

# 새 문단을 서두에 삽입하기 위해 첫 번째 요소 앞에 추가
# python-docx에서는 insert는 어렵지만, 새 문서를 만들고 기존 내용을 복사하는 방식 사용

# 새 문서 생성
new_doc = Document()

# ===== 원페이퍼: 왜 이 과정인가? =====

# 제목
title = new_doc.add_heading('왜 이 과정인가?', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# 서브타이틀
subtitle = new_doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('AI 영상 제작의 본질: 인간이 가장 잘하는 일에 집중하기')
run.bold = True
run.font.size = Pt(14)

new_doc.add_paragraph()

# 섹션 1: 목적
section1 = new_doc.add_heading('목적', level=1)

purpose_text = """이 과정은 바이럴 조회수나 단기 수익화를 위한 교육이 아닙니다.

우리는 AI 시대에 인간이 가장 잘할 수 있는 영역, 즉 '미학적 판단'과 '서사적 감각'에 집중합니다. AI가 아무리 발전해도 "이 장면이 왜 아름다운가", "이 전개가 왜 가슴에 남는가"를 결정하는 건 여전히 인간의 몫입니다.

우리가 제공하는 것:
• 거장의 작품을 해석한 미학 데이터베이스 (왕가위, 타르코프스키, 아케인 시리즈 등)
• 마스터피스 영상들의 색감, 구도, 리듬을 분석한 RAG 데이터셋
• 음악과 영상의 조화를 연구한 논문 기반 사운드 설계 가이드
• 긴 영상에서도 시각적 일관성을 유지하는 동적 프롬프트 시스템

이 모든 것이 하나의 워크플로우 도구로 통합되어, 수강생은 1주차부터 "배우면서 만드는" 것이 아니라 "만들면서 배우는" 방식으로 진입합니다. 첫 주부터 데이터 기반의 맞춤형 오마쥬를 설계하고, 코스 종료 시점에는 3분 애니메이션 뮤직비디오 또는 3분 숏필름을 완성합니다."""

purpose_para = new_doc.add_paragraph(purpose_text)

new_doc.add_paragraph()

# 섹션 2: 방향
section2 = new_doc.add_heading('방향', level=1)

direction_text = """바이럴 콘텐츠 시장은 2024년 반짝 성장 후 포화 상태에 접어들고 있습니다. 우리는 그 다음을 봅니다.

2025년 글로벌 숏폼 드라마 시장은 110억 달러 규모로 전망됩니다(Sensor Tower). 중국, 미국에 이어 한국, 일본에서도 AI 기반 OTT 콘텐츠 수요가 폭발적으로 증가하고 있습니다. 아케인 스튜디오는 이미 AI 숏드라마 제작 계약을 체결했으며, 우리는 그 파이프라인에 투입될 ATC 프로듀서를 양성합니다.

ATC(AI-to-Content) 프로듀서란?
• AI 도구를 활용해 프로덕션급 영상을 기획·제작하는 전문가
• 3분~장편 작품을 AI OTT 플랫폼에 공급하는 크리에이터
• 기술과 미학을 모두 이해하는 "Human-in-the-Loop" 핵심 인력

인턴십 및 취업 연계:
본 과정 우수 수료자는 아케인, M83 스튜디오 등 7개 파트너사의 3개월 인턴십 프로그램에 우선 연결됩니다. 단순 수료가 아닌, 실제 프로젝트 투입을 목표로 합니다."""

direction_para = new_doc.add_paragraph(direction_text)

new_doc.add_paragraph()

# 핵심 문장
highlight = new_doc.add_paragraph()
highlight.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = highlight.add_run('"AI가 90%를 해주는 시대, 당신은 가장 중요한 10%에 집중하세요."')
run.bold = True
run.italic = True
run.font.size = Pt(14)

# 구분선
new_doc.add_paragraph('─' * 50)
new_doc.add_paragraph()

# ===== 기존 문서 내용 복사 =====
for element in doc.element.body:
    new_doc.element.body.append(element)

# 저장
output_path = '/Users/ted/Desktop/AI 영상 제작 클래스 커리큘럼_updated.docx'
new_doc.save(output_path)
print(f'완료: {output_path}')
