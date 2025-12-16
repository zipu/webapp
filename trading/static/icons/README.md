# PWA 아이콘 가이드

이 폴더에는 PWA(Progressive Web App)용 아이콘 파일들이 들어갑니다.

## 필요한 아이콘 파일

1. **icon-192.png** (192x192 픽셀)
   - 홈 화면 아이콘용
   - 안드로이드 기본 아이콘 크기

2. **icon-512.png** (512x512 픽셀)
   - 스플래시 화면용
   - 고해상도 디스플레이 대응

3. **apple-touch-icon.png** (180x180 픽셀)
   - iOS 홈 화면 아이콘용
   - Safari 북마크 아이콘

## 아이콘 생성 방법

### 방법 1: 온라인 도구 사용 (추천)

1. **PWA Icon Generator** - https://tools.crawlink.com/tools/pwa-icon-generator/
   - 하나의 이미지를 업로드하면 모든 크기 자동 생성
   - ZIP 파일로 다운로드 가능

2. **Favicon.io** - https://favicon.io/
   - 텍스트나 이모지에서 아이콘 생성 가능
   - 간단하고 빠름

### 방법 2: 디자인 도구 사용

1. **Figma / Canva**
   - 512x512 캔버스에서 디자인
   - 배경색: #2962FF (앱 테마 색상)
   - 중앙에 심볼 배치 (예: 📊 이모지 또는 "TJ" 텍스트)
   - 여백 10% 유지 (Safe Area)

2. **온라인 이미지 편집기**
   - Photopea (https://www.photopea.com/) - 무료 포토샵 대안
   - Canva (https://www.canva.com/) - 간단한 그래픽 디자인

### 방법 3: Python으로 생성 (개발자용)

```python
from PIL import Image, ImageDraw, ImageFont

# 512x512 아이콘 생성
img = Image.new('RGB', (512, 512), color='#2962FF')
draw = ImageDraw.Draw(img)

# 텍스트 또는 이모지 추가
font = ImageFont.truetype("arial.ttf", 200)
draw.text((256, 256), "📊", fill='white', font=font, anchor='mm')

img.save('icon-512.png')

# 다른 크기로 리사이즈
img_192 = img.resize((192, 192), Image.LANCZOS)
img_192.save('icon-192.png')

img_180 = img.resize((180, 180), Image.LANCZOS)
img_180.save('apple-touch-icon.png')
```

## 디자인 권장 사항

### 색상
- 주 색상: #2962FF (파란색)
- 보조 색상: #764ba2 (보라색)
- 배경: 단색 또는 그라데이션

### 심볼
- 간단하고 인식하기 쉬운 아이콘
- 추천: 📊 (차트), 📈 (상승 그래프), TJ (Trading Journal)
- 여백 유지: 전체 크기의 80% 정도만 사용

### 스타일
- 미니멀리즘
- 명확한 윤곽선
- 고대비 (배경과 심볼)

## 설치 후 확인 방법

1. 파일을 이 폴더에 저장
2. Django collectstatic 실행:
   ```bash
   python manage.py collectstatic --noinput
   ```
3. 모바일 브라우저에서 앱 접속
4. "홈 화면에 추가" 확인

## 트러블슈팅

### 아이콘이 안 보여요
- 브라우저 캐시 삭제 (Ctrl+Shift+Del)
- manifest.json 경로 확인
- 파일 이름 정확히 일치하는지 확인

### iOS에서 아이콘이 다르게 보여요
- apple-touch-icon.png 파일이 있는지 확인
- 180x180 픽셀 정확한 크기인지 확인
- base.html의 apple-touch-icon 링크 태그 확인

## 현재 상태

⚠️ **아이콘 파일이 아직 생성되지 않았습니다.**

이 가이드를 참고하여 아이콘을 생성하고 이 폴더에 추가해주세요.

필요한 파일:
- [ ] icon-192.png
- [ ] icon-512.png
- [ ] apple-touch-icon.png
