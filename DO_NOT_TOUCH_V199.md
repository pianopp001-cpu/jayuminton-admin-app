# v199 보호 규칙

- CSS/HTML/레이아웃/디자인 복구 코드는 수정하지 않는다.
- frame-repair.js, page-repair.js, court-orientation.js는 수정하지 않는다.
- 이번 빌드는 관리자 멤버 등록 시 세션 토큰 전달만 수정한다.
- 빌드 전 diff에서 CSS 관련 변경이 있으면 실패 처리한다.
