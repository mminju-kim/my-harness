# 하네스 역할

## 에이전트

| 이름 | 종류 | 맡는 단계 | 쓰는 도구 |
|---|---|---|---|
| `brief-writer` | 작업 (서브에이전트) | S1 | 파일 읽기·쓰기 |
| `reference-researcher` | 작업 (서브에이전트) | S2 | uibowl 커넥터, Figma |
| `keyscreen-designer` | 작업 (서브에이전트) | S3 | Figma |
| `screen-designer` | 작업 (서브에이전트) | S4 | Figma |
| `judge` | 판정 (서브에이전트 + 스크립트) | M1~M3, S5 | `harness/scripts/judge.py` |
| 오케스트레이터 | 메인 세션 | 순서 진행, 게이트 기록 | 모든 에이전트 호출 |

- 서브에이전트 정의는 `.claude/agents/<이름>.md`에 둔다.

## 편집 범위

| 에이전트 | 고칠 수 있는 것 | 읽기만 하는 것 |
|---|---|---|
| `brief-writer` | `runs/<id>/s1-*` | `docs/` |
| `reference-researcher` | `runs/<id>/s2-*`, Figma `01 References`의 `<id>` 섹션 | `docs/`, `s1-brief.md` |
| `keyscreen-designer` | `runs/<id>/s3-*`, Figma `02 Screens` › `Key Screens`의 `<id>` 섹션 | `docs/`, s1, s2 |
| `screen-designer` | `runs/<id>/s4-*`, Figma `03 Tokens & Components`, `02 Screens` › `Screens`의 `<id>` 섹션 | `docs/`, s1~s3 |
| `judge` | `runs/<id>/s5-verdict.json`만 | 전부 |
| 오케스트레이터 | `runs/<id>/state.json`, `gates.json` | 전부 |

- `docs/`, `harness/rules.json`, `harness/r*.md`는 모든 에이전트가 읽기만 한다. 고치는 건 나만 한다.
- 에이전트는 다른 에이전트의 파일이나 Figma 섹션을 고치지 않는다.

## 판정자

- `harness/scripts/judge.py`, 파이썬 표준 라이브러리만 쓴다.
- 입력: `harness/rules.json` + 스냅샷 파일 (S1·S2는 s1/s2 문서)
- 출력: `runs/<id>/s5-verdict.json` 하나 (M1~M3 결과도 같은 파일에 단계별로 기록)
- Figma 쓰기 도구를 쓰지 않는다. 같은 입력이면 항상 같은 결과가 나온다.
- `judge` 에이전트는 스크립트를 실행하고 결과를 그대로 전달한다. 통과·실패를 바꾸지 않는다.

## 자연어 트리거

| 이렇게 말하면 | 하는 일 |
|---|---|
| "`<화면>` 화면 만들어줘" | 새 실행 시작, S1부터 |
| "이어서 해줘" | `state.json` 기준으로 멈춘 단계부터 |
| "G1 승인" / "G1 반려: `<사유>`" (G2·G3도 같음) | 게이트 기록, 다음 단계 또는 복귀 |
| "판정만 돌려줘" | 현재 스냅샷으로 judge만 실행 |
| "지금 어디까지 했어?" | `state.json`, `gates.json` 요약 |

- 화면 이름은 한글(PRD 16장 이름)이나 화면 id 둘 다 알아듣는다.
