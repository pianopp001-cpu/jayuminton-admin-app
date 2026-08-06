# 자유민턴 GitHub 자동 배포

기존의 `ZIP 다운로드 → 압축 풀기 → 원클릭_강제전체배포.bat 실행`을 GitHub Actions로 옮긴 구성입니다.

## 자동으로 처리되는 작업

- MAIN Apps Script의 현재 코드를 Google에서 다시 가져온 뒤 같은 Deployment ID로 재배포
- PUSH 중계 Apps Script도 같은 방식으로 재배포
- 저장소의 PWA 소스를 Firebase Hosting `jayuminton-push`에 배포
- 실제 MAIN/PUSH/PWA 주소와 v1.6.41 파일 자동 확인

Apps Script를 수정할 때는 변경 파일만 `apps-script-main-overrides` 또는 `apps-script-push-overrides`에 넣으면, 원격 코드를 가져온 후 해당 파일만 덮어써 배포합니다.

## 최초 한 번만 등록할 Repository secrets

저장소에서 `Settings → Secrets and variables → Actions → New repository secret`로 이동해 다음 3개를 등록합니다.

### `JAYUMINTON_DEPLOY_CONFIG_JSON`

현재 PC의 아래 파일 내용을 통째로 등록합니다.

`%LOCALAPPDATA%\JayumintonDeploy\settings.json`

### `CLASPRC_JSON`

현재 PC의 아래 파일 내용을 통째로 등록합니다.

`%USERPROFILE%\.clasprc.json`

기존 `원클릭_최초설정.bat`에서 Apps Script 로그인을 마쳤다면 만들어져 있습니다. 외부에 공개하면 안 됩니다.

### `FIREBASE_SERVICE_ACCOUNT_JSON`

Firebase 프로젝트 `jayuminton-push`에 Hosting 배포 권한이 있는 서비스 계정 JSON 전체를 등록합니다.

## 최초 연결 후

1. 저장소의 `Actions` 탭을 엽니다.
2. `Deploy Jayuminton PWA and Apps Script`를 선택합니다.
3. `Run workflow`를 누르고 `all`을 실행합니다.
4. 초록색 체크가 뜨면 완료입니다.

그 이후에는 제가 `deployment/jayuminton/`의 코드를 GitHub에 반영하면 자동으로 전체 배포됩니다. PC에서 ZIP을 받거나 BAT를 실행할 필요가 없습니다.

## 안전장치

- 세 가지 Secret이 없으면 실제 배포를 하지 않고 정상적으로 건너뜁니다.
- Apps Script는 기존 Deployment ID를 갱신하므로 `/exec` 주소가 바뀌지 않습니다.
- PWA의 필수 파일과 v1.6.41 문자열을 검사한 후에만 Firebase에 올립니다.
- 배포 완료 후 실제 서버 파일까지 다시 검사합니다.
