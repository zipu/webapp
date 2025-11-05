# Echomind Development Notes

## Project Goal
빠른 Activity 로깅 시스템 - 모바일/데스크톱 모두 지원
- 1분에 3-5개 활동 기록 가능한 속도
- 페이지 리로드 없음 (AJAX)
- 모달/리다이렉트 없음
- 확장 가능한 구조 (향후 시각화/분석 추가 예정)

## Database Structure

### Models (echomind/models.py)
1. **Activity_Category**: 활동 카테고리
2. **Status_Tag**: 상태 태그 (ManyToMany)
3. **Activity**: 시간 기반 활동 기록
   - start_time, end_time으로 period 정의
   - duration_in_minutes 자동 계산 (save() 메서드)
4. **Lapse_Category**: 주의력 이탈 카테고리 (level 필드 포함)
5. **Attentional_Lapse**: Activity 내의 주의력 이탈 기록

### Database Configuration
- 앱별 독립 DB 사용
- Database: `echomind` (MySQL)
- Router: `echomind/dbRouter.py` (EchomindDBRouter)
- Settings: `webapp/settings.py` line 180, 226-233

## API Endpoints

### GET /echomind/api/default-times/
최근 activity의 end_time과 현재 시간을 기본값으로 반환
- start_time = 최근 activity의 end_time (없으면 현재 시간)
- end_time = 현재 시간

### POST /echomind/api/activity/create/
Activity 생성
- 입력: category_id, start_time, end_time, description, status_tags[]
- 출력: activity_id, duration (자동 계산)

## Frontend Implementation

### UI Features (echomind/templates/echomind/main.html)
- **카테고리 선택**: 그리드 버튼 레이아웃 (모바일 터치 최적화)
- **시간 입력**: datetime-local, 기본값 자동 채움
- **태그 선택**: 체크박스 스타일 (선택적)
- **제출**: AJAX로 페이지 리로드 없이 제출
- **피드백**: 우측 상단 토스트 메시지 (3초 자동 사라짐)

### JavaScript Flow
1. 페이지 로드 → `/api/default-times/` 호출
2. 카테고리 선택 → 버튼 active 상태
3. 폼 제출 → `/api/activity/create/` POST
4. 성공 → 피드백 표시 + 폼 리셋 + 시간 재로드
5. 바로 다음 활동 입력 가능

## Technical Decisions

### USE_TZ = False
settings.py에서 timezone 사용 안함
- views.py에서 naive datetime 사용 (`datetime.now()`, `datetime.strptime()`)
- `timezone.make_aware()` 사용하지 않음

### Error Handling
- Exception catch → JsonResponse로 에러 반환
- 터미널 디버깅: `print()` + `traceback.print_exc()`
- 프론트엔드에서 에러 메시지 표시

## File Structure
```
echomind/
├── models.py          # 5개 모델 정의
├── views.py           # MainView, API views
├── urls.py            # URL 패턴
├── admin.py           # Admin 등록 (5개 모델)
├── dbRouter.py        # DB 라우터
├── templates/
│   └── echomind/
│       └── main.html  # 빠른 로깅 인터페이스
└── migrations/
    └── 0001_initial.py
```

## Next Steps (미구현)

### Attentional Lapse 로깅
현재 Activity만 구현됨. Lapse 로깅 UI 필요
- Activity 진행 중 실시간 lapse 기록
- 또는 회고적 lapse 입력

### Visualization & Analytics (나중에)
- 시간대별 activity 분포
- 카테고리별 시간 사용량
- Attentional lapse 패턴 분석
- 일/주/월 통계

### Potential Improvements
- 키보드 단축키 지원 (더 빠른 입력)
- 최근 activity 목록 표시
- Bulk edit/delete 기능
- Export to CSV/JSON
- Activity 템플릿 (자주 쓰는 패턴 저장)

## Admin Setup Required
테스트 전 Django admin에서 초기 데이터 생성:
1. Activity_Category (예: Study, Work, Exercise, etc.)
2. Status_Tag (예: Focused, Distracted, Productive, etc.)
3. Lapse_Category (예: Phone, Social Media, Mind Wandering, etc.)

## Known Issues / Resolved
- ✅ duration 필드명 불일치 해결
- ✅ Meta 클래스 정의 수정
- ✅ timezone-aware datetime 에러 해결
- ✅ str 타입 datetime 연산 에러 해결
