# 자유민턴 v1.5 Firebase 개인 배정 알림 설정

## v1.5 동작

- 관리자 앱의 v1.4 TTS와 음악 음량 6단계 동작은 그대로 유지합니다.
- 대기2의 4명이 대기1로 올라오면 선택한 회원 휴대폰에 한 번만 진동·알림을 보냅니다.
- 준비 알림은 `대기 1순위입니다. ○번 코트가 다음으로 나올 예정이니 준비해 주세요.` 형식입니다.
- 예정 코트는 현재 4명이 경기 중인 코트 가운데 `courtStartedAt`이 가장 오래된 코트로 계산합니다.
- 대기1의 4명이 실제 코트로 들어갈 때 해당 회원 휴대폰에 한 번만 진동·입장 알림을 보냅니다.
- 사용자 앱에서 선택한 멤버 ID의 Firebase 주제 하나만 구독합니다.
- 같은 `assignmentId`는 사용자 휴대폰에서 한 번만 처리합니다.
- 음성 다시 재생과 반복 재생은 새 개인 알림을 만들지 않습니다.
- 관리자 앱과 사용자 앱에 현재 창을 다시 불러오는 새로고침 버튼이 있습니다.

## 확인된 Firebase 프로젝트

- Firebase 프로젝트 ID: `jayuminton-push`
- 사용자가 제공한 웹 앱 구성과 Web Push VAPID 공개키는 웹 브라우저 푸시용입니다.
- Android 사용자 APK에는 별도로 등록한 Android 앱의 `google-services.json`이 필요합니다.

## 1. 사용자 Android 앱 등록

1. Firebase Console에서 `jayuminton-push` 프로젝트를 엽니다.
2. `프로젝트 설정 → 일반 → 내 앱 → 앱 추가 → Android`를 선택합니다.
3. Android 패키지 이름을 정확히 `com.jayuminton.member`로 입력합니다.
4. 앱을 등록하고 `google-services.json`을 내려받습니다.
5. 파일 이름을 바꾸지 말고 보관합니다. Git 저장소에는 직접 커밋하지 않습니다.
6. Cloud Functions 배포를 위해 프로젝트가 Blaze 요금제인지 확인합니다.

기본 FCM 알림에는 SHA 인증서 지문을 입력하지 않아도 됩니다.

## 2. Firebase Function 배포

PC에 Node.js 22와 Firebase CLI를 설치한 뒤 저장소 루트에서 실행합니다.

```bash
firebase login
cp .firebaserc.example .firebaserc
firebase use jayuminton-push
```

관리자 앱과 Function이 함께 사용할 충분히 긴 임의 문자열을 정한 뒤 Secret Manager에 저장합니다.

```bash
firebase functions:secrets:set JAYUMINTON_PUSH_SECRET
firebase deploy --only functions:publishAssignment
```

배포가 완료되면 출력되는 `publishAssignment` HTTPS 주소를 보관합니다.

## 3. GitHub Actions Secrets 등록

GitHub 저장소의 `Settings → Secrets and variables → Actions`에서 다음 Repository secrets 세 개를 추가합니다.

### `FIREBASE_GOOGLE_SERVICES_JSON_B64`

PowerShell에서 다음 명령으로 `google-services.json`을 Base64 문자열로 바꾼 값을 등록합니다.

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("google-services.json"))
```

### `JAYUMINTON_PUSH_FUNCTION_URL`

배포 후 받은 `publishAssignment` HTTPS 주소를 그대로 등록합니다.

### `JAYUMINTON_PUSH_SHARED_SECRET`

`firebase functions:secrets:set JAYUMINTON_PUSH_SECRET` 실행 시 입력한 것과 완전히 같은 문자열을 등록합니다.

웹 VAPID 공개키는 위 세 Secret 중 어느 곳에도 넣지 않습니다.

## 4. APK 빌드

세 Secret을 저장한 다음 `v1.5-firebase` 브랜치에 새 커밋이 생기면 `Build v1.5 Firebase APKs`가 실행됩니다. 또는 워크플로를 수동 실행합니다.

완료된 Artifact `jayuminton-v1.5-apks`에는 다음 두 파일이 들어 있습니다.

- `jayuminton-admin-v1.5.apk`
- `jayuminton-member-v1.5.apk`

관리자 APK는 확정된 v1.4 위에 덮어쓰기 설치합니다. 사용자 APK는 알림을 받을 각 회원 휴대폰에 설치합니다.

## 5. 실제 테스트

1. 회원 휴대폰에 사용자 앱을 설치하고 알림 권한을 허용합니다.
2. 사용자 페이지 로그인 후 하단의 `내 이름 선택`에서 본인의 정확한 이름을 선택합니다.
3. 해당 회원이 포함된 대기2가 경기 종료 순환으로 대기1에 올라오게 합니다.
4. 해당 휴대폰에만 대기 1순위 준비 알림이 한 번 표시되는지 확인합니다.
5. 대기1이 실제 코트로 들어갈 때 같은 휴대폰에 코트 입장 알림이 한 번 표시되는지 확인합니다.
6. 관리자 앱에서 음성을 다시 재생하거나 반복해도 같은 배정 알림이 다시 울리지 않는지 확인합니다.
7. 관리자·사용자 앱의 새로고침 버튼이 로그인 상태를 유지한 채 현재 화면을 다시 불러오는지 확인합니다.
