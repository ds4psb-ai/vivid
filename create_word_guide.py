from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Title
title = doc.add_heading('AI 영상 제작 워크플로우 마스터', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('레이아웃 가이드')
run.bold = True
run.font.size = Pt(16)

doc.add_paragraph()

# 전체 레이아웃 구조
doc.add_heading('전체 레이아웃 구조', level=1)

layout_table = doc.add_table(rows=6, cols=1)
layout_table.style = 'Table Grid'
cells = [
    'HEADER - ARKAIN × Crebit 로고 (중앙 정렬)',
    'HERO - "AI 영상 제작 CLASS" 타이틀 + 토끼 캐릭터 + 슬로건',
    'CLASS POINT - 4개 포인트 (2×2 그리드)',
    '영상 클립 삽입',
    'CLASS INFO - 클래스 정보',
    'FOOTER - 가격 / 신청 버튼'
]
for i, text in enumerate(cells):
    layout_table.rows[i].cells[0].text = text

doc.add_paragraph()

# HERO 섹션
doc.add_heading('HERO 섹션 수정사항', level=1)

p = doc.add_paragraph()
run = p.add_run('슬로건 변경\n')
run.bold = True

p = doc.add_paragraph()
p.add_run('기존: ')
p.add_run("'기술' AI 맡기고 '감각'을 깨웁니다.")

p = doc.add_paragraph()
run = p.add_run('변경: ')
run.bold = True
p.add_run('"매주 하나의 완성된 영상을 만들면서, 8개의 AI 도구를 자연스럽게 체득합니다. 4주 후, 당신은 아이디어만 있으면 AI 영상을 혼자 만들 수 있습니다."')

p = doc.add_paragraph()
p.add_run('클래스 레벨: CLASS : A → CLASS : 일반')

doc.add_paragraph()

# CLASS POINT
doc.add_heading('CLASS POINT - 4개 포인트 통합', level=1)

doc.add_paragraph('기존에 개별 배치된 4개 단계를 2×2 그리드로 재배치')

# 2x2 Grid Table
grid_table = doc.add_table(rows=2, cols=2)
grid_table.style = 'Table Grid'
grid_table.rows[0].cells[0].text = '포인트 1 (기획)\n심연의 거울'
grid_table.rows[0].cells[1].text = '포인트 2 (사전제작)\n레퍼런스 해석기'
grid_table.rows[1].cells[0].text = '포인트 3 (제작)\n시나리오 생성기'
grid_table.rows[1].cells[1].text = '포인트 4 (완성)\n퀄리티 디렉터'

doc.add_paragraph()

# 포인트 1
doc.add_heading('포인트 1: 기획 - 심연의 거울', level=2)
doc.add_paragraph('"나를 알아야 내 영상이 나온다"')
p1_table = doc.add_table(rows=3, cols=2)
p1_table.style = 'Table Grid'
p1_table.rows[0].cells[0].text = '핵심'
p1_table.rows[0].cells[1].text = '취향(영화, 음악, 소설)을 AI와 정리하여 "창작 DNA" 분석'
p1_table.rows[1].cells[0].text = '기술'
p1_table.rows[1].cells[1].text = 'Google Gemini 3 Pro, NotebookLM'
p1_table.rows[2].cells[0].text = '예시'
p1_table.rows[2].cells[1].text = '"새벽 산책, 하루키, 왕가위 좋아해요" → "도시의 고독한 낭만주의자" 진단'

doc.add_paragraph()

# 포인트 2
doc.add_heading('포인트 2: 사전제작 - 레퍼런스 해석기', level=2)
doc.add_paragraph('"좋은 건 알겠는데, 뭐가 좋은 건지 모르겠어요"')
p2_table = doc.add_table(rows=3, cols=2)
p2_table.style = 'Table Grid'
p2_table.rows[0].cells[0].text = '핵심'
p2_table.rows[0].cells[1].text = '영상/이미지 분석 → 조명, 색감, 카메라 워킹 인사이트 제공'
p2_table.rows[1].cells[0].text = '기술'
p2_table.rows[1].cells[1].text = 'Google Gemini 3 Pro (멀티모달), NotebookLM'
p2_table.rows[2].cells[0].text = '예시'
p2_table.rows[2].cells[1].text = '강주노 <마더> 분석 → 자연광/실내광 비율, 탈채도 회녹색, 불안/집착'

doc.add_paragraph()

# 포인트 3
doc.add_heading('포인트 3: 제작 - 시나리오 생성기', level=2)
doc.add_paragraph('"대충 이런 느낌인데..."를 구체적인 이야기로')
p3_table = doc.add_table(rows=3, cols=2)
p3_table.style = 'Table Grid'
p3_table.rows[0].cells[0].text = '핵심'
p3_table.rows[0].cells[1].text = 'DNA + 레퍼런스 스타일 = 촬영 가능한 시나리오'
p3_table.rows[1].cells[0].text = '기술'
p3_table.rows[1].cells[1].text = 'Claude 4.5 Opus (논리), Gemini 3 Pro (감성)'
p3_table.rows[2].cells[0].text = '예시'
p3_table.rows[2].cells[1].text = '도시의 고독 + 강주노 = <새벽 3시의 편의점> 시나리오'

doc.add_paragraph()

# 포인트 4
doc.add_heading('포인트 4: 완성 - 퀄리티 디렉터', level=2)
doc.add_paragraph('"프로는 디테일이 다르다"')
p4_table = doc.add_table(rows=3, cols=2)
p4_table.style = 'Table Grid'
p4_table.rows[0].cells[0].text = '핵심'
p4_table.rows[0].cells[1].text = '시각적 일관성, 동작 자연스러움 등 6가지 기준 검수'
p4_table.rows[1].cells[0].text = '기술'
p4_table.rows[1].cells[1].text = '자동 품질 분석, 색보정 제안'
p4_table.rows[2].cells[0].text = '포인트'
p4_table.rows[2].cells[1].text = '혼자 만들어도 프로덕션 퀄리티'

doc.add_paragraph()

# 영상 클립 삽입 위치
doc.add_heading('영상 클립 삽입 위치', level=1)

video_table = doc.add_table(rows=6, cols=3)
video_table.style = 'Table Grid'
headers = ['위치', '영상 타입', '길이']
for i, header in enumerate(headers):
    video_table.rows[0].cells[i].text = header
    
video_data = [
    ['HERO 직후', '하이라이트 티저', '15-30초'],
    ['포인트 1→2 사이', '레퍼런스 분석 예시', '10-15초'],
    ['포인트 3→4 사이', '비포/애프터', '20-30초'],
    ['CLASS INFO 전', '완성 뮤직비디오', '60-90초'],
    ['신청 버튼 전', '수강생 작품 쇼케이스', '30-45초']
]
for row_idx, row_data in enumerate(video_data, 1):
    for col_idx, text in enumerate(row_data):
        video_table.rows[row_idx].cells[col_idx].text = text

doc.add_paragraph()

# CLASS INFO
doc.add_heading('CLASS INFO', level=1)

doc.add_heading('클래스 레벨', level=2)
level_table = doc.add_table(rows=1, cols=3)
level_table.style = 'Table Grid'
level_table.rows[0].cells[0].text = '일반 (현재)'
level_table.rows[0].cells[1].text = '심화 (예정)'
level_table.rows[0].cells[2].text = '전문가 (예정)'

doc.add_paragraph()

doc.add_heading('대상', level=2)
doc.add_paragraph('AI 영상업계 취업 희망자')
doc.add_paragraph('AI 콘텐츠 크리에이터 희망자')
doc.add_paragraph('취업 / 이직 / 포트폴리오 / AI 영상제작')

doc.add_paragraph()

# 스케줄 & 가격
doc.add_heading('스케줄 & 가격', level=1)

schedule_table = doc.add_table(rows=2, cols=2)
schedule_table.style = 'Table Grid'
schedule_table.rows[0].cells[0].text = '일정'
schedule_table.rows[0].cells[1].text = '화/목 월 8회, 19:00-21:00'
schedule_table.rows[1].cells[0].text = '수강료'
schedule_table.rows[1].cells[1].text = '월 24만원'

doc.add_paragraph()

# 추가 도구
doc.add_heading('추가 도구 (통합 가능)', level=1)

extra_table = doc.add_table(rows=5, cols=3)
extra_table.style = 'Table Grid'
extra_table.rows[0].cells[0].text = '도구'
extra_table.rows[0].cells[1].text = '역할'
extra_table.rows[0].cells[2].text = '기술'

extra_data = [
    ['스토리보드 스케치', '장면별 프롬프트 변환', 'Gemini + Claude'],
    ['비주얼 리얼라이저', '첫 프레임 이미지 생성', 'Midjourney, DALL-E 3, Imagen 3'],
    ['비디오 메이커', '이미지→영상 확장', 'Veo 2, Kling, Runway'],
    ['사운드 디자이너', 'BGM/효과음 생성', 'Suno AI, Udio']
]
for row_idx, row_data in enumerate(extra_data, 1):
    for col_idx, text in enumerate(row_data):
        extra_table.rows[row_idx].cells[col_idx].text = text

doc.add_paragraph()

# 컬러 팔레트
doc.add_heading('컬러 팔레트', level=1)

color_table = doc.add_table(rows=7, cols=2)
color_table.style = 'Table Grid'
color_table.rows[0].cells[0].text = '용도'
color_table.rows[0].cells[1].text = 'HEX'

color_data = [
    ['배경 (메인)', '#000000'],
    ['배경 (카드)', '#1A1A1A'],
    ['강조색 1 (골드)', '#FFD700'],
    ['강조색 2 (네온 그린)', '#00FF88'],
    ['텍스트', '#FFFFFF'],
    ['서브 텍스트', '#AAAAAA']
]
for row_idx, row_data in enumerate(color_data, 1):
    for col_idx, text in enumerate(row_data):
        color_table.rows[row_idx].cells[col_idx].text = text

doc.add_paragraph()

# 체크리스트
doc.add_heading('체크리스트', level=1)

checklist = [
    '슬로건 변경',
    'CLASS : A → 일반',
    '4개 포인트 2×2 그리드 통합',
    '영상 클립 5곳 삽입',
    'CLASS INFO 3단계 레벨',
    '가격/신청 버튼 강조'
]

for item in checklist:
    doc.add_paragraph(f'[ ] {item}')

# Save
doc.save('/Users/ted/Desktop/AI영상제작_레이아웃가이드.docx')
print('완료: /Users/ted/Desktop/AI영상제작_레이아웃가이드.docx')
