# 자유민턴 GitHub 자동 배포 설정

이 설정을 완료하면 새 ZIP을 내려받아 압축을 풀고 BAT 파일을 실행할 필요가 없습니다.

- 평소 웹/PWA 수정: GitHub의 `Deploy Jayuminton PWA` 워크플로에서 실행
- `web` 선택: Firebase Hosting만 배포
- `full` 선택: Firebase Hosting 배포 후, 저장소에 존재하는 MAIN/PUSH Apps Script도 기존 배포 ID로 갱신
- 향후 `web-push`, `firebase.json`, `apps-script-main`, `apps-script-push`가 `main`에 들어오면 해당 경로의 변경은 자동 배포

## 1. GitHub Actions Secret 등록

저장소에서 `Settings → Secrets and variables → Actions → Secrets`로 이동합니다.

### 필수: Firebase Hosting

`FIREBASE_SERVICE_ACCOUNT_JAYUMINTON_PUSH`

Firebase Console의 `jayuminton-push → 프로젝트 설정 → 서비스 계정 → 새 비공개 키 생성`에서 받은 JSON 전체를 등록합니다.

서비스 계정에는 Firebase Hosting 배포 권한이 필요합니다. 비공개 키 JSON은 코드에 커밋하거나 채팅에 올리지 않습니다.

### 이미 등록돼 있으면 그대로 사용

`JAYUMINTON_PUSH_APPS_SCRIPT_URL`

PUSH Apps Script의 `/exec` 주소입니다. 기존 APK 빌드에서 사용 중인 Secret이 있으면 새로 만들 필요가 없습니다.

### 전체 배포 시에만 필요

`CLASPRC_JSON`

한 번 `npx --yes @google/clasp@latest login`을 실행한 뒤 생성되는 사용자 홈의 `.clasprc.json` 전체 내용입니다.

`JAYUMINTON_MAIN_MANIFEST_JSON`

기존 원클릭 설정에서 보존한 다음 파일의 전체 내용입니다.

```text
%LOCALAPPDATA%\JayumintonDeploy\main-appsscript.json
```

## 2. GitHub Actions Variable 등록

`Settings → Secrets and variables → Actions → Variables`에 등록합니다. 아래 값은 기존 PC의 파일에서 확인할 수 있습니다.

```text
%LOCALAPPDATA%\JayumintonDeploy\settings.json
```

등록할 이름과 값은 다음과 같습니다.

| GitHub Variable | settings.json 값 |
|---|---|
| `JAYUMINTON_MAIN_WEB_APP_URL` | `mainUrl` |
| `JAYUMINTON_MAIN_SCRIPT_ID` | `mainScriptId` |
| `JAYUMINTON_MAIN_DEPLOYMENT_ID` | `mainDeploymentId` |
| `JAYUMINTON_PUSH_SCRIPT_ID` | `pushScriptId` |
| `JAYUMINTON_PUSH_DEPLOYMENT_ID` | `pushDeploymentId` |
| `JAYUMINTON_PUSH_APPS_SCRIPT_URL` | `pushUrl` — 같은 이름의 Secret이 이미 있으면 Variable은 생략 가능 |

## 3. 실행 방법

1. 저장소 상단 `Actions`를 엽니다.
2. 왼쪽에서 `Deploy Jayuminton PWA`를 선택합니다.
3. `Run workflow`를 누릅니다.
4. 현재 PWA 원본 브랜치는 `v1.5-firebase`를 입력합니다.
5. 보통은 `web`, Apps Script까지 모두 갱신할 때만 `full`을 선택합니다.

워크플로는 배포 전에 필수 파일과 URL 치환을 검사하고, 배포 후 `https://jayuminton-push.web.app`의 실제 응답까지 확인합니다.

## 운영 원칙

- Firebase나 Apps Script 인증정보를 저장소 파일에 직접 쓰지 않습니다.
- `main`에 합치기 전 변경사항을 PR에서 확인합니다.
- 기존 BAT 배포본은 GitHub Actions 장애 시 비상용으로만 보관합니다.
