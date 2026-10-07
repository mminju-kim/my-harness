# 하네스 목적

## 매번 달라지는 것 (입력)

- 대상 화면 1개. PRD 16장 핵심 화면 10개 중 하나를 고른다:
  홈 / 무료 학습자료 / 유료 멤버 자료실 / 스킬 라이브러리 / 미션 상세 /
  제출 화면 / 내 학습 / 내 자산 / 자산 상세 / 운영자 검수 화면
- 고정 입력(매번 같음): `docs/prd.md`, `docs/design.md`, `docs/story-service.md`, `docs/story-work.md`

## 사용자

- 나(디자이너) 1명. Claude Code에서 실행하고 G1·G2·G3를 직접 컨펌한다.
- 내부 관계자 협의는 G2 전에 하네스 밖에서 한다.

## 결과물 형식

- Figma에서 직접 만든다 (Figma 커넥터 `use_figma`).
- 작업 파일 1개, 페이지 3개: `01 References` / `02 Screens` / `03 Tokens & Components`
- `02 Screens`는 Section 두 영역으로 나눈다: `Key Screens` (S3 키스크린), `Screens` (S4 완성 화면)
- 각 단계가 끝나면 Figma의 변수와 노드 속성을 `figma-snapshot.json`으로 내보낸다. 판정 스크립트는 이 파일만 읽는다.
- 예비 경로: Figma 쓰기가 실패하면 3·5단계는 내가 그리고, 하네스는 읽기와 판정만 한다.

## 완료 기준

대상 화면 1개가 Figma에 390×844 프레임으로 있고, `design.md` 판정 위반이 0건이고, `story-service.md`의 A·B 판정 위반이 0건이고, G1·G2·G3가 모두 "승인"으로 기록되면 완료다.
