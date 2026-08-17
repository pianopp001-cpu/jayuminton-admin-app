# 사용자 웹/사용자 앱 운영 보호 및 복구 기준

> 중요: 사용자 웹과 사용자 Android 앱은 운영 핵심 자산이다. 앞으로 변경/복구 시 이 문서를 먼저 확인한다.

## 절대 원칙

1. **사용자 웹과 사용자 앱을 잃거나 임의로 다른 접속 경로로 되돌리지 않는다.**
2. 현재 사용자 접속 구조는 **Cloudflare 경로가 기준**이다. Apps Script `/exec?mode=user` 직접 접속을 사용자 운영 URL로 간주하지 않는다.
3. 운영 장애 시 MAIN Apps Script 버전을 추측해서 롤백하지 않는다. 먼저 Cloudflare frontend / Worker / isolated RPC backend를 각각 분리 진단한다.
4. `HTTP 200`만으로 정상 판정하지 않는다. 실제 RPC 응답에 `ok:true`가 있는지 확인한다.
5. 복구 중 MAIN/관리자/사용자 웹/APK를 한꺼번에 재배포하지 않는다. 장애 범위만 최소 변경한다.
6. 기존 설치 사용자 앱의 접속 경로를 바꾸는 빌드는 명시적 검증 없이 배포하지 않는다.

## 현재 확인된 Cloudflare 사용자 경로

- 사용자 공개 도메인: `https://www.jayfreelab.com`
- Cloudflare Worker RPC: `https://shy-morning-f0e4.pianopp001.workers.dev/`
- Cloudflare용 isolated Apps Script deployment ID: `AKfycbyc1igSCIWFWMLp2qgMGxB4lsSVfcZk3TDk-A6cB3OrQm2fIS7ZLnz8b9jeAIXyCMy-cQ`
- 성공했던 통합 Cloudflare 기준 소스 commit: `1c3aa7a4f77a280805cf43570b3a7f1695998711`
- 해당 isolated backend에는 `memberFirebasePreviewRpc_`가 반드시 존재해야 한다.

## 장애 발생 시 진단 순서

1. 사용자 웹 `www.jayfreelab.com` 실제 접속 확인.
2. Cloudflare Worker RPC에서 `getPublicState` 호출 후 `ok:true` 확인.
3. 동일 요청을 isolated Apps Script deployment에 직접 호출해 `ok:true` 확인.
4. Worker만 실패하면 Worker/라우팅 문제를 수정한다.
5. Worker와 isolated RPC가 모두 성공하는데 앱만 실패하면 Android WebView/앱 내 URL을 조사한다.
6. isolated RPC가 실패할 때만 Cloudflare 전용 backend를 복구한다.
7. MAIN Apps Script는 위 진단으로 MAIN 문제임이 입증되지 않는 한 건드리지 않는다.

## 복구용 Workflow

- `.github/workflows/emergency-restore-cloudflare-rpc-only.yml`
  - Cloudflare 전용 isolated RPC backend만 복구한다.
  - MAIN 운영 deployment, 관리자 deployment, Firebase Hosting, APK를 변경하지 않는다.
  - 복구 후 Apps Script RPC와 Cloudflare Worker RPC 양쪽에서 `ok:true`를 검증한다.

## 금지 사항

- 정상 버전 번호를 확인하지 않고 MAIN deployment를 임의 버전으로 변경 금지.
- Cloudflare 운영 중 Apps Script 직접 사용자 URL을 정상 사용자 URL이라고 안내 금지.
- 사용자 웹 장애를 이유로 APK를 먼저 재빌드/재설치시키지 않는다.
- 기존 정상 사용자 웹/앱을 삭제하거나 덮어쓰기 전에 별도 복구 경로와 검증 없이 진행 금지.
- 과거 Workflow가 현재 secret/config 구조와 맞는지 확인하지 않고 그대로 재실행 금지.

## 이번 장애에서 확인한 교훈

- MAIN Apps Script가 HTTP 200이어도 Cloudflare 사용자 경로의 RPC가 끊기면 사용자에게 `서버에 연결할 수 없습니다`가 표시될 수 있다.
- 사용자 시스템은 MAIN Apps Script 직접 URL만으로 구성된 것이 아니다.
- Cloudflare Worker와 isolated RPC deployment는 사용자 웹/앱의 필수 구성요소로 취급해야 한다.
- 복구 성공 후에는 현재 동작하는 사용자 웹/앱 경로를 기준점으로 보존하고 이후 변경은 최소 단위로 진행한다.
