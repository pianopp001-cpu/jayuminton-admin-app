# 관리자 웹 운영 아키텍처 및 절대 보호 기준

> 이 문서는 관리자 페이지를 복구하거나 변경하기 전에 반드시 확인하는 운영 기준이다.

## 절대 원칙

1. 관리자 페이지는 Google Apps Script `/exec` 페이지가 아니다.
2. 관리자 프런트엔드는 사용자 프런트엔드와 완전히 분리된 독립 웹 페이지다.
3. 관리자 프런트엔드는 관리자 전용 Cloudflare Worker RPC를 통해서만 데이터를 읽고 쓴다.
4. Google Apps Script는 관리자 화면을 제공하지 않고, 격리된 관리자 RPC 백엔드 역할만 한다.
5. 사용자와 관리자는 운영 데이터만 공유한다. HTML, CSS, 화면 구성, 버튼, 기능 흐름과 배포 경로는 공유하지 않는다.
6. 관리자 변경으로 사용자 Hosting 또는 사용자 Worker를 배포하지 않는다.
7. 사용자 변경으로 관리자 프런트엔드 또는 관리자 Worker를 배포하지 않는다.
8. 관리자 페이지 주소로 `script.google.com/macros/s/.../exec`를 안내하거나 저장하지 않는다.
9. 관리자 프런트엔드 안에 iframe 또는 Apps Script 직접 URL이 포함되면 배포를 중단한다.
10. 관리자와 사용자 프런트 파일을 동시에 수정하는 Workflow는 운영에 사용하지 않는다.

## 현재 관리자 Cloudflare 경로

- 현재 관리자 프런트엔드: `https://jayuminton-push--admin-cloudflare-dnhyj6hu.web.app/`
- 관리자 Worker RPC: `https://jayuminton-admin-rpc.pianopp001.workers.dev/`
- 관리자 Worker 이름: `jayuminton-admin-rpc`
- 관리자 프런트 빌드/배포 Workflow: `.github/workflows/preview-admin-cloudflare.yml`
- 관리자 프런트 빌더: `deployment/jayuminton/admin_cloudflare_rpc.py`
- Apps Script deployment는 관리자 전용 RPC 백엔드일 뿐 관리자 웹주소가 아니다.
- 현재 관리자 프런트엔드는 `admin-cloudflare` 독립 채널이며 사용자 production Hosting과 다른 배포 대상이다.

## 사용자 경로와의 분리

- 사용자 Hosting: `https://jayuminton-push.web.app/`
- 사용자 Worker RPC: `https://shy-morning-f0e4.pianopp001.workers.dev/`
- 관리자 Workflow에서는 위 사용자 Hosting과 사용자 Worker를 배포하거나 덮어쓰지 않는다.
- 양쪽에서 동일한 회원·코트·대기 데이터를 보더라도 UI 코드는 서로 독립적으로 유지한다.

## 배포 전 필수 검사

1. 관리자 프런트가 `admin_cloudflare_rpc.py build-frontend`로 생성되는지 확인한다.
2. 생성 결과에 관리자 Worker URL이 포함되는지 확인한다.
3. 생성 결과에 iframe과 `script.google.com/macros/s/`가 없는지 확인한다.
4. 사용자 Hosting production deploy 명령이 관리자 Workflow에 없는지 확인한다.
5. 관리자 vNext 필수 메뉴와 기능 마커가 모두 존재하는지 확인한다.
6. 실제 관리자 Cloudflare 페이지를 열어 로그인 화면과 필수 메뉴를 확인한 뒤에만 성공으로 판정한다.

## 장애 시 금지 사항

- 관리자 장애를 사용자 페이지 재배포로 해결하지 않는다.
- Apps Script `/exec` 주소를 관리자 페이지의 대체 주소로 안내하지 않는다.
- 사용자 프런트의 HTML/CSS/Script를 관리자 복구본으로 사용하지 않는다.
- Workflow 성공만 보고 관리자 기능 복구 성공이라고 말하지 않는다.
