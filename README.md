# Image Overlay

화면 위에 이미지를 띄워두는 프로그램. 크기와 투명도를 조절할 수 있고,
클릭 통과 모드에서는 이미지 위를 클릭해도 아래쪽 창이 그대로 입력을 받는다.

## 기능

- 파일 선택 또는 클립보드 붙여넣기(Ctrl+V)로 이미지 띄우기
- 드래그로 이동, 오른쪽 아래 모서리 드래그 또는 휠로 크기 조절
- 투명도 5~100% 조절
- 항상 위 고정 — 다른 창을 클릭해도 이미지는 사라지지 않음
- 클릭 통과 모드 — 이미지가 마우스 입력을 받지 않아 아래 창에서 그대로 작업 가능
- 이미지 여러 장 동시에 띄우기, 각 이미지 오른쪽 위 X로 닫기

## 요구 사항

- Windows (클릭 통과는 Windows API를 사용한다. 다른 OS에서는 나머지 기능만 동작)
- Python 3.9 이상
- Pillow

```
pip install -r requirements.txt
```

## 실행

```
python overlay.py
```

## 사용법

1. 제어판에서 `파일 열기` 또는 `붙여넣기`로 이미지를 띄운다.
2. 이미지를 드래그해 위치를 맞추고, 휠이나 오른쪽 아래 모서리로 크기를 맞춘다.
3. 투명도 슬라이더로 아래 화면이 비치는 정도를 정한다.
4. 위치가 정해지면 `클릭 통과`를 켠다. 이제 이미지 위를 클릭해도 아래 창이 반응한다.
5. 다시 옮기거나 닫으려면 `클릭 통과`를 끈다. X 버튼이 다시 나타난다.

클릭 통과가 켜져 있는 동안에는 이미지를 마우스로 잡을 수 없으므로,
제어판 창은 닫지 말고 켜둔 채로 사용한다.
## exe로 만들기

### 방법 1 — 빌드 스크립트

`build.bat`을 더블클릭한다. 필요한 패키지를 설치하고 빌드한 뒤
`dist\ImageOverlay.exe`를 만든다. Python만 설치되어 있으면 된다.

### 방법 2 — 직접 명령 실행

```
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --noconsole --onefile --name ImageOverlay overlay.py
```

### 방법 3 — 깃허브에서 자동 빌드

저장소에 푸시하면 `.github/workflows/build.yml`이 Windows 러너에서 exe를 만든다.
Actions 탭 -> 해당 실행 → Artifacts의 `ImageOverlay`를 내려받으면 된다.

만들어진 exe는 Python 없이 단독으로 실행된다. 첫 실행이 몇 초 걸릴 수 있고,
서명이 없어 SmartScreen 경고가 뜨면 `추가 정보 -> 실행`을 누른다.
