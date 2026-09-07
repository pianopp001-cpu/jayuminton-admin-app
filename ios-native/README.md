# 자유민턴 iOS 네이티브 앱

이 폴더는 iPhone용 **네이티브 iOS 앱 셸**입니다. Safari/PWA 설치가 아니라 App Store/TestFlight로 설치되는 앱을 목표로 합니다.

## 운영 경로

- 화면: `https://jayuminton-push.web.app/` (Firebase Hosting)
- 로그인/배정/경기 종료/자리교환/사용자 상태 변경: Cloudflare Worker
- 상태 저장: D1
- 동시 변경 충돌 방지: Durable Objects
- Google Apps Script: **사용하지 않음**

앱은 `WKWebView`로 Firebase Hosting의 현재 사용자 화면을 표시합니다. 핵심 상태 변경은 웹 화면에 이미 연결된 Cloudflare RPC를 그대로 사용하므로 iOS 앱 안에 GAS URL이나 Apps Script deployment ID를 넣지 않습니다.

## 현재 구현

- iPhone 네이티브 앱 (`SwiftUI + WKWebView`)
- Safari 주소창 없이 앱 화면으로 실행
- 현재 운영 사용자 웹을 그대로 표시
- `JayumintonUserNativeIOS/1.0.0` User-Agent 식별자
- `window.NativeUserApp` 호환 브리지 제공
- 회원 선택/푸시 설정/진동 설정 값을 iOS `UserDefaults`에 보관
- 외부 사이트 링크는 Safari/시스템 앱으로 열고 자유민턴 Hosting 내부 이동만 앱 안에서 처리
- CI에서 `script.google.com` 포함 여부를 실패 처리

## 아직 필요한 배포 항목

실제 iPhone에 설치 가능한 IPA/TestFlight/App Store 배포에는 Apple 서명이 필요합니다.

1. Apple Developer Program 계정
2. App Store Connect에 `com.jayuminton.user` 앱 등록
3. Signing Team / 배포 인증서 / Provisioning Profile 또는 App Store Connect API Key
4. App Icon 1024x1024 및 App Store 메타데이터

위 값은 저장소 코드에 직접 넣지 않고 GitHub Actions secret 또는 Xcode 자동 서명을 사용합니다.

## 빌드 검증

```bash
cd ios-native
xcodegen generate
xcodebuild \
  -project JayumintonIOS.xcodeproj \
  -scheme JayumintonIOS \
  -configuration Release \
  -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO \
  build
```

GitHub Actions의 `Validate iOS native app` 워크플로도 같은 방식으로 서명 없이 컴파일 검증합니다.
