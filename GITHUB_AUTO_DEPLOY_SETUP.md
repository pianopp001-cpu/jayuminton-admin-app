# 자유민턴 GitHub 자동 배포 설정

이 설정을 한 번 완료하면 이후에는 ZIP 다운로드, 압축 해제, BAT 실행이 필요 없습니다.

GitHub Actions가 다음 작업을 수행합니다.

1. 현재 운영 중인 MAIN/PUSH Apps Script 원본을 Google에서 직접 가져옵니다.
2. GitHub의 수정 파일이 있으면 해당 파일만 덮어씁니다.
3. 기존 Deployment ID로 재배포하여 `/exec` 주소를 유지합니다.
4. 현재 운영 중인 PWA v1.6.41 파일을 Firebase Hosting에서 직접 가져옵니다.
5. GitHub의 PWA 수정 파일만 덮어쓴 뒤 Firebase Hosting에 배포합니다.
6. MAIN/PUSH/PWA 실제 주소를 다시 열어 배포 결과를 검증합니다.

## 최초 한 번 등록할 GitHub Secrets

저장소에서 다음 경로로 이동합니다.

`Settings → Secrets and variables → Actions → New repository secret`

### 1. JAYUMINTON_DEPLOY_CONFIG_JSON

현재 PC의 아래 파일 내용을 전체 복사해 등록합니다.

```text
%LOCALAPPDATA%\JayumintonDeploy\settings.json
```

이 파일에는 기존 원클릭 배포에서 사용하던 MAIN/PUSH Script ID, Deployment ID, `/exec` 주소, Firebase 프로젝트 ID와 Hosting 주소가 들어 있습니다.

### 2. CLASPRC_JSON

현재 PC의 아래 파일 내용을 전체 복사해 등록합니다.

```text
%USERPROFILE%\.clasprc.json
```

기존 `원클릭_최초설정.bat`에서 Google Apps Script 로그인을 마쳤다면 생성되어 있습니다. 이 값은 Google 계정 인증정보이므로 저장소 파일이나 채팅에 올리지 않습니다.

### 3. FIREBASE_SERVICE_ACCOUNT_JSON

Firebase Console에서 다음 순서로 서비스 계정 비공개 키 JSON을 받습니다.

`jayuminton-push → 프로젝트 설정 → 서비스 계정 → 새 비공개 키 생성`

다운로드한 JSON 파일의 전체 내용을 Secret으로 등록합니다. 서비스 계정에는 Firebase Hosting 배포 권한이 필요합니다.

## 실행 방법

1. 저장소의 `Actions` 탭을 엽니다.
2. `Deploy Jayuminton`을 선택합니다.
3. `Run workflow`를 누릅니다.
4. 전체 강제 배포는 `all`, Firebase 웹만 배포할 때는 `web-only`를 선택합니다.

`deployment/jayuminton/` 아래의 수정 파일이 `main` 브랜치에 반영되면 기본적으로 `all` 전체 배포가 자동 실행됩니다.

## 앞으로 수정 파일을 넣는 위치

| 수정 대상 | GitHub 경로 |
|---|---|
| PWA/Firebase 웹 파일 | `deployment/jayuminton/web-push-overrides/` |
| MAIN Apps Script | `deployment/jayuminton/apps-script-main-overrides/` |
| PUSH Apps Script | `deployment/jayuminton/apps-script-push-overrides/` |
| 배포 버전 | `deployment/jayuminton/RELEASE_VERSION` |

수정하지 않은 파일은 현재 운영 서버와 Google Apps Script에서 직접 가져오므로, 오래된 GitHub 브랜치가 운영 버전을 덮어쓰지 않습니다.

## 안전장치

- 세 가지 Secret 중 필요한 값이 없으면 배포를 시작하지 않습니다.
- 기존 Apps Script Deployment ID를 갱신하므로 사용 중인 `/exec` 주소가 바뀌지 않습니다.
- Firebase 배포 전 `RELEASE_VERSION`과 실제 PWA 파일의 버전이 일치하는지 검사합니다.
- 배포 후 실제 MAIN/PUSH/PWA 주소를 다시 확인합니다.
- 인증정보는 코드에 커밋하지 않습니다.

기존 원클릭 BAT 배포본은 GitHub Actions 장애 시 비상용으로만 보관합니다.
