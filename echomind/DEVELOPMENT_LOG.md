# Echo Mind - Development Log

## 프로젝트 개요
개인용 활동 및 주의력 이탈 기록 앱 (모바일 최적화)

---

## 현재 구조 (2025-11-05 기준)

### URL 구조
```
/echomind/                    → 홈 (대시보드)
/echomind/activity-log/       → Activity 기록 페이지
/echomind/attentional-lapse/  → Lapse 기록 페이지

API:
/echomind/api/default-times/      → Activity 기본 시간 가져오기
/echomind/api/activity/create/    → Activity 생성
/echomind/api/lapse/create/       → Lapse 생성
```

---

## 데이터 모델

### 1. Activity 관련 모델
```python
Activity_Category
  - name: 활동 대분류 (자기계발, 운동, 업무 등)
  - description

Activity_Tag
  - name: 활동 세부 내용 (독서, 코딩, 러닝, 헬스 등)
  - description

Status_Tag
  - name: 주관적 평가 (피곤함, 집중력 높음, 즐거움 등)

Activity
  - category: FK to Activity_Category
  - start_time
  - end_time
  - duration_in_minutes (자동 계산)
  - activity_tags: M2M to Activity_Tag (활동 내용)
  - status_tags: M2M to Status_Tag (주관적 평가)
  - description
```

### 2. Lapse 관련 모델
```python
Lapse_Category
  - name: Lapse 카테고리 (유튜브, 폰, SNS 등)
  - description

Attentional_Lapse
  - lapse_type: 선택 필드
    * 'passive lapse' (Passive Lapse)
    * 'narrative drift' (Narrative Drift)
    * 'intentional lapse' (Intentional Lapse)
    * 'affective lapse' (Affective Lapse)
  - timestamp (자동 생성)
  - category: FK to Lapse_Category
  - activity: FK to Activity (자동 연결)
  - duration_in_minute
  - description
```

---

## 주요 기능

### 1. Activity 기록
**워크플로우:**
1. Category 선택 (필수)
2. Start Time / End Time 입력 (한 줄에 2컬럼)
3. Activity Tags 선택 (선택, 복수 가능)
4. Status Tags 선택 (선택, 복수 가능)
5. Description 입력 (선택)
6. 저장 시 자동 처리:
   - duration_in_minutes 자동 계산
   - 해당 시간대의 Lapse 자동 연결

**특징:**
- 이전 Activity의 end_time을 다음 Activity의 start_time으로 자동 설정
- 모바일 최적화된 큰 터치 영역

### 2. Lapse 기록
**워크플로우:**
1. 현재 시각 실시간 표시
2. Lapse Type 선택 (필수, 4개 버튼)
3. Category 선택 (선택)
4. Duration 입력 (선택)
5. Description 입력 (선택)

**특징:**
- 빠른 입력에 최적화
- timestamp 자동 생성
- Activity 저장 시 자동으로 해당 시간대의 Lapse와 연결됨

**사용 패턴:**
- Lapse 발생 즉시 기록 → Activity 종료 시 기록
- Activity가 Lapse를 포함하는 관계

### 3. 자동 Lapse 연결
Activity 생성 시 자동 실행:
```python
# start_time ~ end_time 사이의 연결 안된 Lapse들을 자동 연결
lapses = Attentional_Lapse.objects.filter(
    timestamp__gte=start_time,
    timestamp__lte=end_time,
    activity__isnull=True
).update(activity=activity)
```

---

## UI/UX 특징

### 모바일 최적화
- 하단 고정 네비게이션 바 (엄지 접근성)
- 큰 터치 영역의 버튼들
- 반응형 그리드 레이아웃
- 16px 이상 폰트 크기 (자동 줌 방지)

### 네비게이션
```
🏠 Home | ⚡ Lapse | 📝 Activity
```

### 홈 화면
- 2개의 큰 버튼 카드
  - Record Lapse (보라색 그라디언트)
  - Log Activity (핑크 그라디언트)

### 공통 템플릿
- `echomind/base.html`:
  - 공통 스타일
  - 하단 네비게이션
  - 피드백 메시지 시스템

---

## 파일 구조

```
echomind/
├── models.py
│   ├── Activity_Category
│   ├── Activity_Tag (새로 추가)
│   ├── Status_Tag
│   ├── Activity
│   ├── Lapse_Category
│   └── Attentional_Lapse
├── views.py
│   ├── HomeView
│   ├── ActivityLogView
│   ├── LapseLogView
│   ├── get_default_times()
│   ├── create_activity()
│   └── create_lapse()
├── urls.py
├── admin.py
└── templates/echomind/
    ├── base.html (공통 템플릿)
    ├── home.html
    ├── activity_log.html
    └── lapse_log.html
```

---

## 마이그레이션 히스토리

### 0003_remove_lapse_category_level_and_more
- Lapse_Category에서 level 필드 제거
- Attentional_Lapse에 lapse_type 필드 추가

### 0004 (최신)
- Activity_Tag 모델 추가
- Activity에 activity_tags M2M 필드 추가
- Status_Tag M2M에 related_name 추가

---

## 디자인 결정사항

### 1. Category vs Tag 분리
- **Activity_Category**: 대분류 (자기계발, 운동 등)
- **Activity_Tag**: 세부 활동 (독서, 코딩 등)
- **Status_Tag**: 주관적 평가 (피곤함, 집중 등)

**이유:**
- 같은 대분류 내에서도 세부 활동이 다름
- 데이터 분석 시 유연성 확보

### 2. Lapse Level → Lapse Type
- 필드명을 `level`에서 `lapse_type`으로 변경
- Lapse_Category에서 Attentional_Lapse로 이동

**이유:**
- 같은 행동(예: 유튜브)도 맥락에 따라 다른 type
- "level"은 단계/정도를 의미하지만, 실제로는 서로 다른 "종류"

### 3. Lapse → Activity 자동 연결
- Activity 저장 시 시간대 기반 자동 연결

**이유:**
- Lapse는 발생 즉시 기록 (빠름)
- Activity는 종료 후 기록 (느림)
- 수동 연결은 불편하고 에너지 소모

---

## 다음 개발 예정 사항

### [2025-11-06] Activity Timeline 페이지 (우선순위: 높음)

**목표:**
- 하루 동안의 activity를 시각적으로 확인할 수 있는 타임라인 뷰 제공
- 날짜별 이동 기능으로 과거 기록 탐색

**Phase 1: 일간 타임라인 뷰**

**UI/UX 설계:**
- 세로 컬럼 형태로 00:00 ~ 23:59 시간축 표시
- 각 activity를 시작/종료 시간에 맞춰 블록으로 시각화
- 블록 높이 = 시간 길이에 비례
- 카테고리별 색상 구분
- 빈 시간은 회색 배경으로 표시

**주요 기능:**
1. **날짜 네비게이션**
   - 상단에 날짜 표시 (예: "2025년 11월 6일")
   - 좌측 화살표 (←): 전날 이동
   - 우측 화살표 (→): 다음날 이동
   - 날짜 클릭 → 달력 피커 오픈
   - "오늘" 버튼으로 빠른 복귀

2. **Activity 블록 표시**
   - 카테고리명 + 시간 표시 (예: "공부 2.5h")
   - 클릭 시 상세정보 모달
     - Description
     - Activity Tags
     - Status Tags
     - 해당 시간대 Lapses (있을 경우)

3. **하루 요약 (상단)**
   - 카테고리별 총 시간 (바 차트 또는 파이 차트)
   - 총 활동 시간 / 빈 시간 비율

4. **Lapse 표시**
   - 타임라인 상에 작은 아이콘으로 표시 (⚡)
   - 클릭 시 Lapse 상세정보

**구현 계획:**

**1. Backend (views.py)**
```python
# 새로운 View & API 추가
- ActivityTimelineView: 타임라인 페이지 렌더링
- get_activities_by_date(): 특정 날짜의 모든 activity 조회
  - 파라미터: date (YYYY-MM-DD)
  - 리턴: activities list (JSON)
```

**2. Frontend (activity_timeline.html)**
- 날짜 네비게이션 헤더
- 00:00~23:59 시간축 생성 (세로)
- Activity 블록 동적 생성 및 배치
- JavaScript로 API 호출 & 렌더링
- 모달 팝업 (상세정보)

**3. URL 추가**
```
/echomind/timeline/ → ActivityTimelineView
/echomind/api/activities/by-date/ → get_activities_by_date
```

**4. 네비게이션 업데이트**
- 하단 네비게이션에 "📊 Timeline" 추가

**모바일 최적화 고려사항:**
- 터치 제스처: 좌우 스와이프로 날짜 이동
- 타임라인 세로 스크롤 최적화
- 블록 최소 높이 설정 (짧은 activity도 탭 가능하게)
- 글자 크기 충분히 크게 (16px+)

**Phase 2: 주간 타임라인 뷰 (차후 구현 예정)**

**컨셉:**
- 7일치를 세로로 쌓아서 배치
- 각 날짜마다 축약된 타임라인
- 특정 날짜 탭하면 일간 상세 뷰로 전환
- 전체 패턴 파악에 유용

**구현 방식:**
- 일간/주간 탭으로 뷰 전환
- 또는 별도 페이지로 분리
- 모바일에서 자연스러운 세로 스크롤 활용

**결정 보류:**
- 일간 뷰 사용 경험 후 필요성 재검토
- 주간 뷰의 정보 밀도 vs 가독성 트레이드오프 검토

---

### 통계 & 분석 (홈 화면 예정)
- 시간대별 활동 분석
- Lapse 패턴 분석
- Category/Tag별 시간 통계
- Lapse type별 분포

### 향후 고려사항
- 데이터 export 기능
- 차트/그래프 시각화
- 기간별 필터링
- 목표 설정 및 추적

---

## 기술 스택
- Django (Python)
- Bootstrap 4.2.1
- Vanilla JavaScript
- SQLite (개발/개인용)

---

## 운영 노트
- 개인 사용 목적 (배포 고려 안함)
- 모바일 환경 주 사용
- 사용 편의성 최우선
- 입력 에너지 최소화
