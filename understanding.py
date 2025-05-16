from nudenet import NudeDetector

print(dir(NudeDetector))      # A 안에 있는 이름들의 리스트
help(NudeDetector)            # A 모듈 전체에 대한 문서화된 설명

import nudenet


if hasattr(nudenet, 'NudeClassifier') and callable(getattr(nudenet, 'NudeClassifier')):
    print("nudenet 라이브러리에 B 함수가 존재합니다.")
else:
    print("nudenet 라이브러리에 B 함수가 존재하지 않습니다.")