# 자유민턴 GitHub 자동 배포

이 폴더는 기존의 `압축 풀기 → 원클릭_강제전체배포.bat 실행` 절차를 GitHub Actions로 옮긴 것입니다.

## 자동 배포 범위

- MAIN Google Apps Script 코드 업로드 및 기존 `/exec` 배포 갱신
- PUSH 중계 Google Apps Script 코드 업로드 및 기존 `/exec` 배포 갱신
- Firebase Hosting `jayuminton-push` 배포
- 배포 후 MAIN/PUSH/PWA 주소와 v1.6.41 파일 자동 확인

## 최초 한 번만 등록할 Repository secrets

GitHub 저장소에서 `Settings → Secrets and variables → Actions → New repository secret`로 이동해 다음 3개를 등록합니다.

### 1. `JAYUMINTON_DEPLOY_CONFIG_JSON`

현재 PC의 아래 파일 내용을 통째로 등록합니다.

`%LOCALAPPDATA%\JayumintonDeploy\settings.json`

이 파일에는 MAIN/PUSH의 Script ID, 기존 Deployment ID, `/exec` 주소, Firebase 프로젝트와 Hosting 주소가 들어 있습니다.

### 2. `CLASPRC_JSON`

현재 PC의 아래 파일 내용을 통째로 등록합니다.

`%USERPROFILE%\.clasprc.json`

기존 `원클릭_최초설정.bat`에서 Google Apps Script 로그인을 마쳤다면 생성되어 있습니다. 이 값은 외부에 공개하면 안 됩니다.

### 3. `FIREBASE_SERVICE_ACCOUNT_JSON`

Firebase 프로젝트 `jayuminton-push`에 배포 권한이 있는 서비스 계정 JSON 전체를 등록합니다. 최소한 Firebase Hosting 배포 권한이 필요합니다.

## 최초 연결 후 실행

1. GitHub 저장소의 `Actions` 탭을 엽니다.
2. `Deploy Jayuminton PWA and Apps Script`를 선택합니다.
3. `Run workflow`를 누르고 `all`을 선택합니다.
4. 초록색 체크가 뜨면 연결 완료입니다.

그 이후에는 `deployment/jayuminton/`의 배포 패키지가 main 브랜치에 반영될 때 자동으로 전체 배포됩니다. 웹만 다시 올릴 때는 Actions에서 `web-only`를 선택할 수 있습니다.

## 안전장치

- 세 가지 Secret이 등록되지 않았으면 실제 배포를 하지 않고 정상 종료합니다.
- 배포 패키지의 필수 파일과 버전 문자열을 먼저 검사합니다.
- 기존 Apps Script Deployment ID를 갱신하므로 사용 중인 `/exec` 주소가 바뀌지 않습니다.
- Firebase 배포 후 실제 서버 파일에서 v1.6.41과 `setup-v208.js`를 다시 확인합니다.
