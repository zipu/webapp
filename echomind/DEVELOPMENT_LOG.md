# Echo Mind - Development Log

## 프로젝트 개요
개인용 활동 및 주의력 이탈 기록 앱 (모바일 최적화)

---

## 현재 구조 (2025-11-06 기준)

### URL 구조
```
/echomind/                    → 홈 (대시보드)
/echomind/activity-log/       → Activity 기록 페이지
/echomind/attentional-lapse/  → Lapse 기록 페이지
/echomind/timeline/           → Activity 타임라인 (일간 뷰)
/echomind/plan/               → 계획 관리 페이지
/echomind/stats/              → 통계 및 분석 페이지

API:
/echomind/api/default-times/         → Activity 기본 시간 가져오기
/echomind/api/activity/create/       → Activity 생성
/echomind/api/lapse/create/          → Lapse 생성
/echomind/api/activities/by-date/    → 날짜별 Activity 조회
/echomind/api/plans/by-date/         → 날짜별 Plan 조회
/echomind/api/plan/create/           → Plan 생성
/echomind/api/plan/delete/           → Plan 삭제
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
  - lapse_type: 선택 필드 (Lapse Type과 연결)
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

### 3. Plan 모델
```python
Plan
  - date: 계획 날짜
  - category: FK to Activity_Category
  - estimated_hours: 예상 시간 (Decimal)
  - note: 메모
  - created_at (자동 생성)
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
- `get_net_duration()` 메서드: Activity 시간에서 Lapse 시간을 뺀 순수 활동 시간 계산

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
- Lapse Type 선택 시 해당 타입의 Category만 필터링되어 표시

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

### 4. Activity Timeline (일간 타임라인)
**워크플로우:**
1. 날짜 선택 (전일/다음날/오늘/날짜 피커)
2. 00:00~23:59 타임라인 시각화
3. Activity 블록 표시 (시간 비례)
4. Activity 상세 정보 확인

**특징:**
- **수면 시간 최적화**: 00:00~06:00 구간 축소 표시 (토글 가능)
- **활동 블록**: 카테고리별 색상 구분, 시간 비례 높이
- **자정 넘김 처리**: 23:30~00:30 같은 활동을 양일에 올바르게 표시
- **터치 제스처**: 좌우 스와이프로 날짜 이동 (수평 스와이프만 감지)
- **Activity 리스트**: 타임라인 하단에 카드 형태로 상세 정보 표시
  - Category, 시간, duration, net duration
  - Activity/Status Tags
  - 연결된 Lapses

**API:**
- `get_activities_by_date`: 특정 날짜의 모든 Activity 및 연결된 Lapse 정보 조회

### 5. Plan 관리
**워크플로우:**
1. 날짜 선택 (Timeline과 동일한 네비게이션)
2. 카테고리별 계획 시간 입력
3. 실제 Activity와 자동 비교

**특징:**
- **예상 vs 실제 비교**: 같은 날짜의 Activity 데이터와 자동 매칭
- **차이 표시**: 초과/부족 시간을 색상으로 구분
  - 양수(초과): 녹색
  - 음수(부족): 빨간색
- **메모 기능**: 계획별 노트 추가 가능
- **카테고리 색상**: Timeline과 동일한 색상 체계 사용

**API:**
- `get_plans_by_date`: 날짜별 Plan 조회 및 실제 Activity 비교
- `create_plan`: 새 계획 생성
- `delete_plan`: 계획 삭제

### 6. 통계 및 분석 (Stats)
**기간 선택:**
- 오늘 / 이번주 / 이번달

**주요 지표:**
1. **요약 카드 (2x2 그리드)**
   - 총 활동 시간
   - 순수 활동 시간 (Lapse 제외)
   - Lapse 시간
   - 집중률 (%)

2. **카테고리 분석**
   - 카테고리별 시간 및 비율
   - 수평 막대 차트 (CSS only)
   - 시간 많은 순으로 정렬

3. **Lapse 분석**
   - 총 Lapse 횟수
   - 평균 지속 시간
   - Lapse Type별 분포 (횟수 및 비율)

4. **계획 달성률**
   - 전체 달성률 표시
   - 카테고리별 달성률 막대 차트
   - 색상 코드:
     - 녹색 (≥90%): 우수
     - 노란색 (70-90%): 양호
     - 빨간색 (<70%): 미달

**구현 특징:**
- 서버 사이드 계산 (Django ORM)
- 순수 CSS 시각화 (외부 라이브러리 없음)
- 새 모델 없음 (기존 데이터 활용)

---

## UI/UX 특징

### 모바일 최적화
- 하단 고정 네비게이션 바 (엄지 접근성)
- 큰 터치 영역의 버튼들
- 반응형 그리드 레이아웃
- 16px 이상 폰트 크기 (자동 줌 방지)

### 네비게이션
```
📝 Log | 📊 Timeline | 📅 Plan | 📈 Stats
```
- **Log**: Home, Lapse, Activity 통합
- **Timeline**: 일간 타임라인 뷰
- **Plan**: 계획 관리
- **Stats**: 통계 및 분석

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
│   ├── Activity_Tag
│   ├── Status_Tag
│   ├── Activity (+ get_net_duration 메서드)
│   ├── Lapse_Category (+ lapse_type 필드)
│   ├── Attentional_Lapse
│   └── Plan
├── views.py
│   ├── HomeView
│   ├── ActivityLogView
│   ├── LapseLogView
│   ├── ActivityTimelineView
│   ├── PlanView
│   ├── StatsView
│   ├── get_default_times()
│   ├── create_activity()
│   ├── create_lapse()
│   ├── get_activities_by_date()
│   ├── get_plans_by_date()
│   ├── create_plan()
│   └── delete_plan()
├── urls.py
├── admin.py
└── templates/echomind/
    ├── base.html (공통 템플릿 + PWA)
    ├── home.html
    ├── activity_log.html
    ├── lapse_log.html
    ├── activity_timeline.html
    ├── plan.html
    └── stats.html
```

---

## 마이그레이션 히스토리

### 0003_remove_lapse_category_level_and_more
- Lapse_Category에서 level 필드 제거
- Attentional_Lapse에 lapse_type 필드 추가

### 0004
- Activity_Tag 모델 추가
- Activity에 activity_tags M2M 필드 추가
- Status_Tag M2M에 related_name 추가

### 0005
- Lapse_Category에 lapse_type 필드 추가 (default='passive lapse')
- Lapse_Category의 name unique 제약 제거

### 0006 (최신)
- Plan 모델 추가

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

## 개발 완료 내역

### [2025-11-06] Stats 페이지 구현 ✅
- 기간별 통계 (오늘/이번주/이번달)
- 요약 카드: 총 시간, 순수 시간, Lapse 시간, 집중률
- 카테고리 분석 with CSS 막대 차트
- Lapse 분석 (타입별 분포, 평균 지속시간)
- 계획 달성률 시각화

### [2025-11-06] Plan 관리 페이지 구현 ✅
- Plan 모델 추가
- 날짜별 계획 생성/삭제
- 예상 vs 실제 시간 비교
- 차이 시각화 (색상 코드)

### [2025-11-06] Activity Timeline 페이지 구현 ✅
- 일간 타임라인 뷰
- 날짜 네비게이션
- 수면 시간 축소 표시
- 자정 넘김 활동 처리
- 터치 제스처 (좌우 스와이프)
- Activity 상세 카드 뷰

### [2025-11-06] Lapse Category 개선 ✅
- Lapse_Category에 lapse_type 필드 추가
- Lapse Type 선택 시 Category 필터링

### [2025-11-05] Activity 모델 개선 ✅
- get_net_duration() 메서드 추가
- Lapse 시간 제외한 순수 활동 시간 계산

### [2025-11-05] PWA 기능 추가 ✅
- Service Worker 등록
- 홈 화면 설치 배너
- 모바일 앱처럼 사용 가능

---

## 다음 개발 예정 사항

### 주간 타임라인 뷰 (차후 검토)
**컨셉:**
- 7일치를 세로로 쌓아서 배치
- 각 날짜마다 축약된 타임라인
- 특정 날짜 탭하면 일간 상세 뷰로 전환
- 전체 패턴 파악에 유용

**결정 보류:**
- 일간 뷰 사용 경험 후 필요성 재검토
- 주간 뷰의 정보 밀도 vs 가독성 트레이드오프 검토

### 향후 고려사항
- 데이터 export 기능 (CSV, JSON)
- 목표 설정 및 추적 기능
- 알림/리마인더 기능
- 카테고리 색상 커스터마이징
- Dark mode

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
