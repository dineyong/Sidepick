# SIDEPICK 기기별 개발 환경

SIDEPICK은 공식 네이버 API로 상품 후보를 조사하는 Python PoC다. 맥과 Windows에서 코드를 공유할 수 있지만 SQLite 관측 이력과 결과 보고서는 각 기기에 저장된다.

## 저장소와 작업 브랜치

- GitHub: https://github.com/dineyong/Sidepick
- 회사 폴더: `C:\Users\USER\Documents\New project\SidePick`
- 2026년 10월 8일 확인한 브랜치: `main`, 커밋 `cceed24`.
- Python 3.10 이상. 의존성은 `requirements.txt`를 사용한다.

맥에서 처음 받을 때:

```sh
git clone --branch main https://github.com/dineyong/Sidepick.git SidePick
cd SidePick
```

## 회사 Windows

저장소 루트에서 실행한다. 이미 가상환경이 있으면 재사용한다.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
.\.venv\Scripts\python.exe -m sidepick.cli --help
```

## 맥북 M1

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; fi
.venv/bin/python -m sidepick.cli --help
```

가상환경은 각 기기에서 새로 만든다. 위 도움말 명령은 수집을 실행하지 않는다. 맥 M1에서의 실제 실행 검증은 남아 있다.

## 설정과 실제 수집

`.env`에 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`을 각 기기에서 설정한다. 트렌드 분석에는 `SIDEPICK_CATEGORY_ID_AUTO`, `SIDEPICK_CATEGORY_ID_LIVING`, `SIDEPICK_CATEGORY_ID_CAMPING`도 필요하다. 카테고리 ID가 없으면 해당 트렌드 점수가 0으로 처리될 수 있다.

실제 API 호출과 DB 저장을 진행할 때만 아래 명령을 사용한다.

```powershell
# Windows
.\.venv\Scripts\python.exe -m sidepick.cli discover --top 20
```

```sh
# macOS
.venv/bin/python -m sidepick.cli discover --top 20
```

## 이력과 보고서 공유

`data/sidepick.db`, `reports/latest.html`, `reports/latest.json`은 Git에서 제외된다. 맥에서 새 DB로 실행하면 회사에서 쌓인 스냅샷을 이어받지 못해 이력에 의존하는 분석 결과가 달라질 수 있다.

기존 이력을 이전하려면 수집과 DB 사용을 종료한 뒤 SQLite 백업을 만들고 별도로 전달해 복원한다. 다른 기기의 기존 DB를 덮어쓰기 전에 보존한다. 두 기기에서 수정한 DB를 단순 파일 복사로 병합하지 않는다. 결과 공유만 필요하면 HTML 또는 JSON 보고서를 별도로 전달한다.
## 작업 시작과 종료

작업 시작 시 저장소 루트에서 아래 명령으로 현재 브랜치와 변경 사항을 확인한다.

```sh
git status --short --branch
git fetch origin
git branch --show-current
```

미커밋 변경이 있으면 먼저 내용을 확인한다. 변경을 버리거나 다른 기기의 작업을 덮어쓰지 않는다. 현재 브랜치가 원하는 작업 브랜치이고 로컬 변경이 정리됐으면 `git pull --ff-only`로 최신 코드를 받는다. 실패하면 분기된 커밋을 확인하고 해결한다. 브랜치는 작업 내용을 확인한 뒤 선택하며, 기존 작업 폴더의 브랜치를 무조건 바꾸지 않는다.

AI에게 작업을 맡길 때는 다음과 같이 요청한다.

> README.md, docs/work-environment.md, docs/handoff.md와 연결된 현황 문서를 읽어줘. 현재 브랜치와 로컬 변경을 확인하고 다음 작업을 진행해줘.

작업 종료 시 `docs/handoff.md`에 변경 내용, 검증 결과, 남은 문제, 다음 작업을 갱신한다. 비밀 값과 원본 운영 로그는 기록하지 않는다. 변경 파일을 검토해 필요한 코드와 문서만 명시적으로 stage하고 커밋한 뒤 해당 작업 브랜치를 push한다. 다른 기기에서 이어가기 전에 push 성공을 확인한다.

`.env`, 가상환경, 설치된 의존성, DB와 실행 중인 프로세스는 Git으로 공유되지 않는다. 맥과 Windows에서 의존성을 각각 설치하고 비밀 값은 각 기기에 따로 설정한다. DB 이력을 이어받으려면 별도의 백업과 복원이 필요하다. MCP를 연결해도 이 데이터가 자동으로 동기화되지는 않는다.
