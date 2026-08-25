# Jayuminton Project Rules

## 최우선 기준
현재 프로젝트의 기능·배포·UI 판단 기준은 `PROJECT_SPEC_20260825.md`이다.

이 문서는 사용자가 2026-08-25 업로드한 `관리자_사용자(7).md`를 기준으로 저장한 최신 운영 명세다.
서로 충돌하는 과거 규칙, MD(4), MD(5), GAS snapshot, 이전 APK 버전 메모, 이전 대화의 완료 주장은 `PROJECT_SPEC_20260825.md`보다 우선할 수 없다.

과거 감사 문서는 참고만 하며, 새 수정은 반드시 최신 명세와 현재 main 소스를 다시 대조한 뒤 진행한다.

## 운영 구조
- Google Apps Script를 운영 런타임으로 사용하지 않는다.
- 과거 GAS 코드는 기능 참고/이식용으로만 사용할 수 있다.
- 로그인, 배정, 경기 종료, 자리교환, 사용자 상태 변경, 관리자 메시지 전송은 Cloudflare Worker를 사용한다.
- 회원·코트·대기열·게임횟수·설정·백업·사용자 공개메모·팀 정보는 D1을 기준 저장소로 사용한다.
- 사용자와 관리자의 동시 변경 충돌은 Durable Objects를 통해 직렬화한다.
- 사용자 APK 알림·진동은 Firebase FCM을 사용한다.
- 앱 미설치 사용자는 현재 사용자 웹 화면에서 팝업·진동을 제공한다.
- Firebase Hosting은 현재 사용자 웹 화면의 호스팅에 사용할 수 있지만, 핵심 상태 변경/저장 런타임은 Cloudflare를 기준으로 한다.

## 공식 운영 고정점 (2026-08-25)
아래 4개 경로만 현재 운영 UI/APK 기준이다. 파일명에 과거 버전 숫자가 포함되어 있더라도 아래 성공 Run이 검증된 기준이며, 이름만 보고 더 오래된 체인으로 교체하거나 롤백하지 않는다.

백엔드 상태 서비스의 최신 검증 고정점은 `.github/workflows/deploy-cloudflare-state-shadow.yml` Run `32791638372`이다. 이 Run에서 Cloudflare-only, D1, Durable Object, stale 부분교환 보호, 자동배정 함께 경기통계 1회 기록, 경기종료 대기열 승급 계약을 테스트한 뒤 운영 Worker를 배포하고 라이브 health까지 검증했다.

1. 관리자 웹
   - workflow: `.github/workflows/deploy-cloudflare-admin-save-lock-memo.yml`
   - verified run: `32756280670`
   - baseline: v203
   - source: `releases/jayuminton-admin-v200.8-webview-js-fixed.apk` 내부 검증 HTML + v203 bridge + V24 post-contract
   - runtime: Cloudflare-only / GAS absent

2. 관리자 APK
   - workflow: `.github/workflows/build-v2015-known-good-shell.yml`
   - verified run: `32791676287`
   - SHA256: `cd1215003cb5969744369c5b4bdfce1d5bc0b01298e71c21584dd505f17bb387`
   - 실제 산출물 기준: admin v203.0 complete pair recording / unobstructed team cards / latest Cloudflare V24 contract
   - workflow 파일명의 `v2015`는 과거 이름일 뿐 운영 버전을 뜻하지 않는다. 이를 이유로 v201.x로 롤백하지 않는다.

3. 사용자 웹
   - workflow: `.github/workflows/deploy-md6-self-longpress-production.yml`
   - verified run: `32753455501`
   - 기준 기능: 자기카드 긴누름, 상태변경, 내정보/공개메모, 사용자 팀 스트라이프, Cloudflare 상태 연동

4. 사용자 APK
   - workflow: `.github/workflows/build-user-md-final-v1642.yml`
   - verified run: `32791897059`
   - release: `1.6.42`
   - SHA256: `d99e17eaff0395ae2f3d5576054f84780c0d1de6f485451a84fab5789d9726b2`
   - 기준 기능: Cloudflare 상태 연동 + Durable Object 대상 토큰 + FCM + 선택된 본인 대상 알림 + 3회×8묶음 진동 + 확인 즉시 중지

### 운영 금지 / 회귀 금지 경로
- `.github/workflows/build-apk.yml`의 과거 v199.x/GAS 계열을 운영 빌드로 사용하지 않는다.
- `.github/workflows/build-v2006-md-clean-final.yml`의 과거 v201.4 관리자 APK 빌드는 봉인 상태를 유지하며 운영 빌드로 사용하지 않는다.
- `fix/pwa-v1641-source` 브랜치의 v1.6.41 `deploy-pwa.yml`은 GAS/clasp를 포함한 과거 경로이므로 운영 배포에 사용하지 않는다.
- `script.google.com/macros/s/`, Apps Script deployment ID, `clasp pull/push/create-deployment`가 최종 운영 경로에 다시 들어가면 회귀로 판정한다.
- v199.x, v200.x, v201.x 명칭의 과거 APK/워크플로를 최신 운영본보다 우선하지 않는다.
- 이미 차단한 과거 GAS/lightweight 사용자 APK, 옛 관리자 음성/빌드 체인을 다시 활성화하지 않는다.
- 관리자 웹/APK의 v203 핵심 기능을 라이브 HTML 위에 중복 주입하지 않는다. 검증 원본에서 재현 가능한 순서로 빌드한다.

## 관리자 APK
- 관리자 APK는 Cloudflare 운영 경로에 직접 연결되어야 한다.
- `script.google.com`, Apps Script deployment ID, `clasp`를 최종 APK 운영 의존성으로 넣지 않는다.
- PIN 원문을 저장하지 않고 30일 인증 세션을 재사용한다.
- 기본적으로 관리자 폰에는 사용자용 진동/팝업을 보내지 않는다.
- 관리자가 사용자로 본인을 설정한 경우에만 본인의 대기1/코트 알림·진동을 받을 수 있어야 한다.
- 저장중에는 일반 조작을 차단하되 음성제어 영역은 항상 동작해야 한다.

## 사용자 웹 / 사용자 APK
- 사용자 웹·APK는 Cloudflare 상태 경로를 사용한다.
- 비밀번호가 바뀌지 않는 동안 인증 세션을 유지해 재접속 때 자동 진입한다.
- 사용자 APK는 실제 FCM token을 발급하고 선택된 본인 memberId와 연결해야 한다.
- 백그라운드/화면 꺼짐 상태를 포함해 대기1 및 코트배정 알림을 받을 수 있어야 한다.
- 알림 진동은 최신 명세의 3회 × 8회 규칙과 확인 즉시 중지 규칙을 따른다.
- 자기카드 긴누름 메뉴, 공개 메모, 빈자리 이동, 자리교환 요청 기능은 실제 Worker 상태 변경과 연결되어야 한다.

## 동시성/저장 우선순위
- 사용자가 자신의 위치를 직접 변경한 최신 서버 상태를 우선한다.
- 관리자는 그 최신 상태를 다시 읽고 남은 자리만 수동/자동 배정한다.
- 부분 자리교환은 실행 순간 실제 원래 그룹에 남아 있는 회원만 대상으로 하며, 사용자가 먼저 이동해 stale 상태가 된 선택 ID는 건너뛴다.
- 배정, 경기종료, 자리교환, 사용자 상태 변경, 메모 변경은 Durable Object를 통해 충돌 없이 직렬화한다.
- 화면의 로컬 상태만 바뀐 것을 완료로 간주하지 않는다. D1 반영 후 최신 서버 상태를 다시 받아 양쪽 화면을 갱신한다.

## 경기종료 / 통계 / 알림 계약
- 경기종료 시 일반 코트와 0명 코트 모두 대기1→코트, 대기2→대기1 순으로 승급한다.
- 코트에 새로 진입한 회원의 게임횟수와 함께 경기통계를 서버 기준으로 기록한다.
- 자동배정의 함께 경기통계는 요청 단위 전후 상태를 기준으로 정확히 한 번만 기록한다. 내부 이동마다 중복 기록하지 않는다.
- 코트로 승급한 회원은 `court_assignment`, 새 대기1이 된 회원은 `wait1_ready` 대상이 된다.
- 푸시 Worker는 이벤트에 포함된 대상 회원 ID의 등록 토큰만 조회해 FCM을 전송한다.
- 사용자 APK는 현재 선택된 본인 memberId와 targetMemberId가 일치할 때만 알림/소리/3×8 진동을 실행하고 확인 즉시 중지한다.

## UI/기능 변경 원칙
- 최신 `PROJECT_SPEC_20260825.md`에 명시된 UI·기능은 기존 화면과 다르더라도 최신 명세에 맞게 구현한다.
- 최신 명세에 없는 불필요한 디자인 변경은 하지 않는다.
- 사용자 웹/앱의 기존 정상 기능을 깨지 않도록 기능 단위로 변경하고 회귀검증한다.
- 카드의 이름/닉네임/신규/찬조/팀/메모 표기 규칙을 임의로 축약하거나 숨기지 않는다.
- 백엔드 함수 존재만으로 완료 처리하지 않는다. 실제 관리자 UI, 사용자 UI, APK, 배포 경로까지 연결되어야 PASS이다.

## 완료 판정
완료라고 말하기 전에 현재 `main`에서 다음을 확인한다.
1. `PROJECT_SPEC_20260825.md` 요구사항과 1:1 대조.
2. 실제 소스/워크플로/배포 경로 존재 확인.
3. Cloudflare-only 핵심 운영 경로 확인.
4. 상태전이 회귀테스트 확인.
5. 사용자 FCM token 등록 및 알림 경로 확인.
6. 관리자/사용자 APK 빌드 검증.
7. 생성·수정했다고 말한 파일을 다시 fetch하여 실제 main 반영 확인.
8. 사용자 상태 변경과 관리자 저장이 동시에 발생했을 때 최신 사용자 상태가 덮어써지지 않는지 확인.
9. 저장중 오버레이가 일반 입력을 막으면서 음성제어는 계속 가능한지 확인.
10. 사용자 공개 메모와 관리자 카드 반영, 팀 표시, 경기통계 전체 펼침이 실제 UI에서 누락 없이 보이는지 확인.
11. 작업 전후에 위 '공식 운영 고정점' 4개 중 의도하지 않은 축이 옛 워크플로/버전으로 바뀌지 않았는지 확인.
12. 최종 HTML/APK에 `script.google.com/macros/s/`가 포함되지 않았는지 확인.
13. 자동배정 pair_stats가 요청당 1회만 기록되는지 회귀테스트 확인.
14. `court_assignment`/`wait1_ready`가 대상 회원에게만 전달되고 사용자 APK가 현재 선택된 본인에게만 3×8을 실행하는지 push 계약 테스트 확인.

확인되지 않은 항목은 PASS로 기록하지 않는다.