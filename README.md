# NSFW 영상 분석기

AI를 활용한 실시간 NSFW 콘텐츠 탐지 및 영상 정화 도구입니다.

## 주요 기능

- **실시간 영상 분석**: URL 입력으로 실시간 NSFW 탐지 및 자동 정지
- **로컬 영상 분석**: 업로드된 영상에서 NSFW 구간 제거 및 깨끗한 영상 생성
- **통합 GUI**: 하나의 인터페이스에서 두 가지 기능 모두 사용 가능

## 설치 방법

### 1. Python 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 시스템 요구사항

#### Chrome 브라우저 설치
- [Google Chrome](https://www.google.com/chrome/) 최신 버전 설치

#### ChromeDriver 설치
```bash
# macOS (Homebrew 사용)
brew install chromedriver

# 또는 수동 다운로드
# https://chromedriver.chromium.org/ 에서 Chrome 버전에 맞는 드라이버 다운로드
# PATH에 추가하거나 프로젝트 폴더에 배치
```

#### FFmpeg 설치 (영상 편집용)
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# Windows
# https://ffmpeg.org/download.html 에서 다운로드 후 PATH 추가
```

### 3. Apple Silicon Mac 사용자 추가 설정

```bash
# Apple Silicon에서 PyTorch 최적화
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

## 사용 방법

### 메인 애플리케이션 실행

```bash
python main.py
```

### 개별 모듈 실행

**실시간 분석만 사용:**
```bash
python nsfw_realtime.py
```

**로컬 영상 분석만 사용:**
```bash
python nsfw_video.py
```

## 설정 옵션

- **NSFW 탐지 임계값**: 0~100 (기본값: 50)
  - 낮을수록 민감하게 탐지
  - 높을수록 확실한 경우만 탐지

## 출력 파일

### 실시간 분석
- `NSFW_detected_[시간]s_[신뢰도]percent.png`: 탐지된 프레임 파일

### 로컬 영상 분석
- `nsfw_analysis_[타임스탬프]/`: 분석 결과 폴더
  - `clean_video_[타임스탬프].mp4`: 정화된 영상
  - `nsfw_analysis_report_[타임스탬프].txt`: 상세 분석 보고서


## 라이선스

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

## 주의사항

- 이 도구는 AI 기반 탐지이므로 100% 정확하지 않을 수 있습니다
- 중요한 용도로 사용하기 전에 충분한 테스트를 권장합니다
- YouTube 이용약관을 준수하여 사용하세요 