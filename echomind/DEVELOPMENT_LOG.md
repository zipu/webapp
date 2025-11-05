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
