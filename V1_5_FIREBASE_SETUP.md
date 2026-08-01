# 자유민턴 v1.5 무료 Firebase 개인 배정 알림 설정

> 이 방식은 Firebase Cloud Functions와 Blaze 요금제를 사용하지 않습니다.
> 무료 Google Apps Script가 FCM HTTP v1 API를 호출합니다.

## v1.5 동작

- 확정된 v1.4 관리자 TTS와 음악 음량 6단계 동작을 그대로 유지합니다.
- 대기2의 4명이 대기1로 올라오면 선택한 회원 휴대폰에 한 번만 진동·알림을 보냅니다.
- 준비 알림은 `대기 1순위입니다. ○번 코트가 다음으로 나올 예정이니 준비해 주세요.` 형식입니다.
- 예정 코트는 현재 4명이 경기 중인 코트 가운데 `courtStartedAt`이 가장 오래된 코트로 계산합니다.
- 대기1의 4명이 실제 코트로 들어갈 때 해당 회원 휴대폰에 한 번만 진동·입장 알림을 보냅니다.
- 사용자 앱에서 선택한 멤버 ID의 Firebase 주제 하나만 구독합니다.
- 같은 `assignmentId`는 사용자 휴대폰에서 한 번만 처리합니다.
- 음성 다시 재생과 반복 재생은 새 개인 알림을 만들지 않습니다.
- 관리자 앱과 사용자 앱에 현재 창을 다시 불러오는 새로고침 버튼이 있습니다.

## 준비된 항목

- Firebase 프로젝트 ID: `jayuminton-push`
- Android 사용자 앱 패키지: `com.jayuminton.member`
- GitHub Repository secrets
  - `FIREBASE_GOOGLE_SERVICES_JSON_B64`
  - `JAYUMINTON_PUSH_SHARED_SECRET`

## 1. Firebase 서비스 계정 비공개 키 받기

1. Firebase Console에서 `jayuminton-push` 프로젝트를 엽니다.
2. `프로젝트 설정 → 서비스 계정`으로 이동합니다.
3. `Firebase Admin SDK → 새 비공개 키 생성`을 누릅니다.
4. 내려받은 JSON 파일을 안전한 PC 폴더에 보관합니다.

이 파일은 Firebase 발송 권한이 있는 비공개 키입니다.

- 채팅에 올리지 않습니다.
- GitHub에 커밋하지 않습니다.
- 다른 사람에게 전달하지 않습니다.
- Apps Script의 Script Property에만 저장합니다.

## 2. 무료 Google Apps Script 발송기 만들기

1. 브라우저에서 `https://script.new`를 엽니다.
2. 프로젝트 이름을 `자유민턴 개인 알림`으로 정합니다.
3. 저장소의 `apps-script-push/Code.gs` 전체를 기본 `Code.gs`에 붙여 넣습니다.
4. 왼쪽 `프로젝트 설정`에서 `편집기에 appsscript.json 매니페스트 파일 표시`를 켭니다.
5. 저장소의 `apps-script-push/appsscript.json` 전체를 Apps Script의 `appsscript.json`에 붙여 넣습니다.

## 3. Apps Script 속성 두 개 등록

Apps Script의 `프로젝트 설정 → 스크립트 속성 → 스크립트 속성 추가`에서 등록합니다.

### `JAYUMINTON_PUSH_SHARED_SECRET`

GitHub Repository secret에 등록한 것과 완전히 같은 긴 문자열을 넣습니다.

### `FCM_SERVICE_ACCOUNT_JSON`

1단계에서 받은 서비스 계정 JSON 파일을 메모장으로 열고, 중괄호 `{`부터 마지막 `}`까지 전체 내용을 넣습니다.

저장 후 편집기 상단 함수 목록에서 `verifyPushConfiguration`을 선택하고 `실행`합니다. 처음 한 번 외부 요청 권한을 승인합니다.

실행 기록에 오류 없이 완료되면 서비스 계정과 FCM 인증이 정상입니다.

## 4. Apps Script를 웹 앱으로 배포

1. 오른쪽 위 `배포 → 새 배포`
2. 유형에서 `웹 앱`
3. 다음 사용자로 실행: `나`
4. 액세스 권한: `모든 사용자`
5. `배포`
6. 발급된 `/exec`로 끝나는 웹 앱 URL을 복사합니다.

웹 앱 URL을 브라우저로 열었을 때 다음과 비슷한 JSON이 보이면 정상입니다.

```json
{"ok":true,"service":"jayuminton-free-fcm-relay","projectId":"jayuminton-push"}
```

## 5. 마지막 GitHub Secret 등록

GitHub 저장소의 `Settings → Secrets and variables → Actions → New repository secret`에서 추가합니다.

```text
Name: JAYUMINTON_PUSH_APPS_SCRIPT_URL
Secret: Apps Script에서 발급된 /exec 웹 앱 URL
```

관리자 APK 빌드 시 이 URL 뒤에 공유 보안키를 안전하게 URL 인코딩하여 붙입니다. 기존 네이티브 알림 브리지는 그대로 사용합니다.

## 6. APK 빌드

`v1.5-firebase` 브랜치의 `Build v1.5 Firebase APKs` 워크플로를 실행합니다.

완료된 Artifact `jayuminton-v1.5-apks`에는 다음 두 파일이 들어 있습니다.

- `jayuminton-admin-v1.5.apk`
- `jayuminton-member-v1.5.apk`

관리자 APK는 확정된 v1.4 위에 덮어쓰기 설치합니다. 사용자 APK는 알림을 받을 회원 휴대폰에 설치합니다.

## 7. 실제 테스트

1. 회원 휴대폰에 사용자 앱을 설치하고 알림 권한을 허용합니다.
2. 사용자 페이지 로그인 후 하단의 `내 이름 선택`에서 본인의 정확한 이름을 선택합니다.
3. 해당 회원이 포함된 대기2가 경기 종료 순환으로 대기1에 올라오게 합니다.
4. 해당 휴대폰에만 대기 1순위 준비 알림이 한 번 표시되는지 확인합니다.
5. 대기1이 실제 코트로 들어갈 때 같은 휴대폰에 코트 입장 알림이 한 번 표시되는지 확인합니다.
6. 관리자 앱에서 음성을 다시 재생하거나 반복해도 같은 배정 알림이 다시 울리지 않는지 확인합니다.
7. 관리자·사용자 앱의 새로고침 버튼이 로그인 상태를 유지한 채 현재 화면을 다시 불러오는지 확인합니다.
