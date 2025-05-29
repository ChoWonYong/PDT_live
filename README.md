# NSFW 영상 분석 시스템

## 🔧 실행 안내

프로그램을 실행하면 몇 줄의 Warning 이후 `tkinter` 기반의 '모드 선택 창'이 출력됩니다.

![모드 선택 창](https://github.com/user-attachments/assets/7ba51fa2-9f71-4945-89e3-5b84525d8a38)

## 🌐 URL 입력 모드

- URL 입력창이 `tkinter`를 통해 표시됩니다.
- URL을 입력하면 셀레니움 기반의 영상 제어 창이 실행됩니다.

![URL 입력 모드](https://github.com/user-attachments/assets/c716aa37-3c6c-4bde-a45f-700c26bdada2)

- 외설 감지 시 다음과 같은 제어 기능이 작동합니다:
    - 10초 전으로 되돌리기
    - 영상 일시정지
    - 전체화면 모드 종료

## 📁 영상 파일 분석 모드

- 사용자가 로컬에서 비디오 파일을 선택할 수 있는 창이 표시됩니다.
- 선택된 영상에 대해 NSFW 탐지가 시작됩니다. (프레임 간격은 조정 가능)

![영상 파일 분석 선택](https://github.com/user-attachments/assets/195509fa-5ee8-4605-8759-f426af4092e6)

- 분석 결과는 `.txt` 형식의 리포트로 저장됩니다.
    - 외설적인 장면이 한 번도 감지되지 않았다면, "외설 없음"으로 저장됩니다.
    - 외설적인 장면이 감지되면 발생 시간대와 함께, 각 구간의 NSFW 확률이 기록됩니다.

![레포트 저장 예시](https://github.com/user-attachments/assets/e21e1a2f-3a78-4a90-8f15-32c1faf5cfc3)