# 서비스별 데이터 참조 가이드

7개 백엔드 서비스(Product / Ingredients / Diet / Recipe / Community / Admin / Main)가 `service-db-v1.0`(schema `service`) 및 외부 User/Auth 서비스(schema `public`, `test_db`)의 데이터를 어떻게 참조해야 하는지 정리한다. User/Auth 서비스 자체는 이미 별도로 존재하며 이번 분리 대상이 아니다.

## 테이블 소유권 매트릭스

| 테이블 | 소유 서비스 | 비고 |
|---|---|---|
| `public.users` / `social_accounts` / `admin_accounts` | User/Auth (외부, 기존) | 이 저장소가 다루는 대상 아님. 모든 서비스는 JWT의 `user_id`(INTEGER)만 신뢰하고 읽는다 |
| `service.products`, `service.product_tags` | **Product** | `product_tags`는 Product가 쓰기를 담당하되 `tag_id` 유효성은 Ingredients가 관리하는 `tags`를 참조 |
| `service.tags` | **Ingredients** | CATEGORY/ALLERGEN/SWEETENER/HEALTH_LABEL 코드북. Product/Main/Community가 읽기 전용으로 참조 |
| `service.user_health_profiles`, `service.user_preferences` | **Main** | 로그인 유저가 입력한 건강/선호 정보를 기준으로 홈 화면 맞춤 정보(당/칼로리 게이지 등)를 내려줘야 하므로 Main이 소유 (2026-07-15 팀 결정) |
| `service.meal_logs`, `service.meal_items`, view `service.v_meal_totals` | **Diet** | `meal_items.product_id`는 Product 데이터의 스냅샷 참조 |
| `service.user_favorites` | Diet 또는 User 쪽 후보 (아래 참고) | `product_id`(Product)와 `external_recipe_id`(Recipe)를 동시에 참조하는 경계 테이블 |
| 레시피 콘텐츠 (제목/재료/조리법 등) | **Recipe** | 이 DB에 테이블 없음 — Recipe Service가 자체 스토리지를 가져야 함 |
| 커뮤니티 게시글/좋아요 | **Community** | 이 DB에 테이블 없음 — Community Service가 자체 스토리지를 가져야 함 |
| (없음) | **Admin** | 자체 데이터 테이블 없음. 각 서비스의 관리자 권한 API를 호출하는 BFF |
| (없음) | **Main** | 자체 데이터 테이블 없음(단, 위 건강프로필/선호 제외). 홈 화면 집계용 BFF |
| 검색기록·비교기록·AI 관심패턴 등 분석 데이터 | (Admin이 조회만) | Kafka→MongoDB 파이프라인 (`docs/user-event-schema.md`), Postgres에는 없음 |

## 열린 이슈 (진행 전 팀 내 확인 필요)

1. ~~`user_health_profiles`/`user_preferences`의 소유 서비스가 미정이다.~~ **해결(2026-07-15): Main Service 소유로 확정.** 로그인 유저가 입력한 정보로 Main이 맞춤형 정보를 내려줘야 하기 때문.
2. **`public.users`와 데이터가 중복될 수 있다.** 실제 `public.users`에 이미 `favorite_categories VARCHAR[]`, `is_allergic BOOLEAN`, `tall`, `weight` 컬럼이 있다 — `service.user_health_profiles`/`user_preferences`가 정규화해서 표현하려는 것과 같은 정보다. User/Auth 팀과 단일 진실 공급원을 정해야 한다. 자세한 내용은 `../09-schema-fix-log.md` 참고.
3. **`user_favorites`의 소유가 애매하다.** 아래 각 서비스 문서에서 Diet Service가 잠정 소유하는 것으로 기술했지만, User 쪽에 두는 안도 가능하다.

## 서비스별 상세 문서

- [product-service.md](./product-service.md)
- [ingredients-service.md](./ingredients-service.md)
- [diet-service.md](./diet-service.md)
- [recipe-service.md](./recipe-service.md)
- [community-service.md](./community-service.md)
- [admin-service.md](./admin-service.md)
- [main-service.md](./main-service.md)
