# 자유민턴 v199 PIN 수정 작업 체크포인트

## 작업 목적
정상 v199 디자인과 동작을 그대로 유지하면서, 관리자 로그인 후 멤버 등록 완료 시 `관리자 PIN이 틀렸습니다.`가 발생하는 문제만 수정한다.

## 절대 변경 금지
- v199 기존 디자인
- 기존 버튼 위치
- 기존 글자 크기
- 기존 코트 배치 UI
- 기존 아이콘
- Firebase/알림/진동 연결 구조
- 사용자 Apps Script 5개 파일의 전체 디자인

## 프로젝트 구조
- 관리자 Android APK: v199 디자인 유지 및 관리자 기능
- 코트배정 Apps Script: `Code.gs`, `Admin.html`, `Index.html`, `Script.html`, `Style.html`
- 개인 알림 Apps Script/Firebase: 별도 배포 및 연결

## 확인된 정상 원본
정상 v199 APK 내부에서 다음 4개 디자인 런타임을 확인함.
- `admin-runtime.js`
- `court-orientation.js`
- `frame-repair.js`
- `page-repair.js`

## 확인된 오류 원인
관리자 로그인 성공 후 저장되는 값은 PIN 문자열 자체가 아니라 관리자 세션 토큰이다. 추가 멤버 등록 기능이 별도 스크립트 범위에서 이 값을 읽지 못해 빈 값이 전달되면서 `관리자 PIN이 틀렸습니다.` 오류가 발생한다.

## 수정 원칙
- 로그인 성공 세션 토큰을 `window`, `localStorage`, `sessionStorage`에 공유
- 멤버 등록 시 동일 토큰을 읽어 전달
- 디자인 관련 HTML/CSS/레이아웃은 수정하지 않음

## 현재 작업 브랜치
`fix/v199-pin-gradle`

## 현재 상태
- 별도 브랜치 생성 완료
- 잘못 생성된 placeholder asset 제거 완료
- Gradle 패키지명 확인: `com.jayuminton.admin`
- Gradle 릴리스 서명 설정 확인 완료
- 아직 최종 Actions 성공 APK 없음

## 실패 이력
- 잘린 base64 데이터로 ZIP 복원 실패
- 17KB 불완전 APK를 원본으로 사용해 런타임 누락
- 재포장 APK는 Android 설치 관리자에서 거부됨

## 다음 작업
1. 정상 v199 런타임 4개를 Android assets에 직접 반영
2. 세션 토큰 공유 패치 반영
3. Gradle 정식 release 빌드
4. Actions 초록 체크 확인
5. 아티팩트 직접 다운로드
6. 설치 가능한 APK 전달

## 금지
- 새 UI 재작성 금지
- Apps Script 전체 디자인 수정 금지
- 중간 실패 빌드를 완료라고 말하지 않기
- 성공 확인 전 APK 제공하지 않기
