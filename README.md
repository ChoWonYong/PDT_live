실행시 몇 줄의 Warning 이후 , 모드 선택창 출력(tkinter)

![스크린샷 2025-05-29 132708](https://github.com/user-attachments/assets/7ba51fa2-9f71-4945-89e3-5b84525d8a38)
영상 파일 분석보드 선택 시 사용자의 로컬파일을 선택할 수 있는 창 출력, 이후 사용자가 선택한 비디오형식의 파일에 대한 nsfw 탐시 시작(프레임간격조정가능)
![스크린샷 2025-05-29 132723](https://github.com/user-attachments/assets/195509fa-5ee8-4605-8759-f426af4092e6)
이후 그 결과를 txt로 레포트형식으로 저장. 외설이 한번도 없다면 그냥 외설이 아님을 저장하고, 외설이 하나라도 있을 시에는, 해당 외설이 나타나는 시간대와 각각의 nsfw 확률을 알려줌
![스크린샷 2025-05-29 132738](https://github.com/user-attachments/assets/e21e1a2f-3a78-4a90-8f15-32c1faf5cfc3)
만약 모드 선택창에서 URL 입력 모드 선택 시, URL 입력할 수 있는 tkinter 창을 전시하고, URL 입력시에는, 기존 셀레니움 모델처럼 제어가능한 영상창을 출력하고, 외설 감지시, 10초 전으로 되돌리기/영상멈추기/전체화면 축소하기
![스크린샷 2025-05-29 133158](https://github.com/user-attachments/assets/c716aa37-3c6c-4bde-a45f-700c26bdada2)
