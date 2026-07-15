# Admin Service

## 소유 데이터

**없음.** Admin Service는 자체 테이블을 갖지 않는 BFF(Backend-for-Frontend)로 설계한다. 관리자 로그인 자체도 이미 외부 User/Auth 서비스의 `public.admin_accounts`/`public.users`가 처리한다 — 이 서비스가 별도 관리자 계정 테이블을 다시 만들 필요가 없다.

## 하는 일

각 도메인 서비스의 "관리자 권한이 필요한" API를 대신 호출해주는 게이트웨이 역할.

| 기능ID | 설명 | 실제 데이터를 갖는 곳 |
|---|---|---|
| AD-0101~0102 | 상품 등록/수정 | **Product Service** 호출 (`service.products`) |
| AD-0103 | 영양성분 등록 | **Product Service** 호출 (`service.products` 영양 컬럼) |
| AD-0104 | 원재료·알레르기 등록 | **Product Service**(`ingredient_text`) + **Ingredients Service**(태그) 둘 다 호출 |
| AD-0109~0112 | 검색기록/비교기록/AI 관심패턴/선택경향 분석 | **이 DB(Postgres)에 없음.** `docs/user-event-schema.md`에 정의된 Kafka→MongoDB 이벤트 스트림에서 읽는다. Admin Service는 이 파이프라인의 분석/집계 API(또는 별도 analytics 서비스)를 호출 |
| AD-0113 | 개선 제안 요약 | 위 이벤트 분석 결과를 요약해서 보여주는 것 — 별도 저장 안 함 |
| AD-0114 | 모니터링 대시보드 | 애플리케이션 DB가 아니라 인프라 관측 스택(메트릭/로그/트레이스) 연동 — OP/CI 영역 |

## 왜 자체 테이블을 두지 않는가

- 상품/영양성분/원재료는 전부 Product·Ingredients 도메인의 데이터라, Admin이 별도로 들고 있으면 두 곳에 진실이 생긴다.
- 검색기록·비교기록 같은 사용자 행동 분석은 처음부터 Postgres가 아니라 이벤트 스트림(Mongo) 쪽에 설계돼 있다 — Admin이 Postgres에 새 분석 테이블을 만드는 건 기존 설계와 어긋난다.
- 결과적으로 Admin Service의 역할은 "권한 검증(관리자 role 확인) + 여러 서비스의 쓰기 API를 조합해서 호출"로 좁혀진다.

## 구현 시 참고

- 관리자 권한 검증(SC-0102)은 User/Auth 서비스가 내려주는 JWT의 role 클레임(`public.admin_accounts` 연동 결과)을 그대로 신뢰하면 된다.
- AD-0101/0102처럼 Product Service에 프록시하는 엔드포인트는 Product Service 쪽에 "관리자 전용" 경로를 별도로 열어두고, Admin Service는 그 앞단에서 권한만 검증한 뒤 그대로 전달하는 얇은 레이어로 두는 걸 권장한다.
