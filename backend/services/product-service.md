# Product Service

## 소유 데이터

- `service.products` (23컬럼, PK `product_id` UUID)
- `service.product_tags` (PK `(product_id, tag_id)`)

쓰기는 이 서비스만 한다. 다른 서비스는 이 두 테이블에 직접 INSERT/UPDATE하지 않는다.

## 참조하는 외부 데이터 (읽기 전용)

- `service.tags` — **Ingredients Service 소유**. 검색/상세 응답에 태그 이름·설명을 채울 때 조인해서 읽는다. `tag_id`는 쓰되 `tag_name`/`description`/`caution_text`는 절대 이 서비스가 갱신하지 않는다.

## 반드시 지켜야 할 제약

- **CATEGORY 개수 트리거**: `products` insert와 그 상품의 CATEGORY 태그 insert(`product_tags`, `tags.tag_type='CATEGORY'`)를 **같은 트랜잭션**에서 처리해야 한다. `ctr_product_category_after_product`/`ctr_product_category_after_tag`가 `DEFERRABLE INITIALLY DEFERRED`라 COMMIT 시점에 "이 상품 CATEGORY 태그가 정확히 1개인가"를 검사한다. 트랜잭션을 나누면 커밋 시점에 뜬금없이 실패한다.
- `product_tags.tag_id`를 넣기 전에 해당 `tag_id`가 `service.tags`에 실제로 존재하고 `active=true`인지 확인한다(Ingredients Service API 호출 또는 같은 DB 내 조인).
- `commerce_product_id`는 UNIQUE — 판매처 재크롤링/재등록 시 upsert 키로 사용.
- 신규 상품 `product_id`를 원본 크롤링 데이터와 동일 규칙으로 재현하려면 `UUIDv5(NAMESPACE_URL, "service-db-v1.0/product/{commerce_product_id}")`를 쓴다. 그럴 필요 없는 신규 등록 상품은 `gen_random_uuid()`로도 충분하다.

## 담당 기능 (기능명세서 기준)

| 기능ID | 설명 | 참고 |
|---|---|---|
| MN-0102 | 홈 통합 검색 | `PR-0101`과 동일 검색 로직 재사용 |
| PR-0101~0105 | 검색, 자동완성, 카테고리/주의성분 필터, 정렬 | `products` + `product_tags` JOIN `tags` |
| PR-0201~0203 | 상품 상세, 영양성분, 원재료/알레르기 | `products` 컬럼 직접 반환 |
| PR-0301~0306 | AI 한줄요약/감미료 설명/맞춤 설명/대용량 추천/리뷰 | AI 요약은 런타임 생성(저장 안 함). **PR-0306 상품 리뷰는 이 DB에 테이블이 없다** — 신규 테이블 설계 필요 |
| AD-0101~0102 | 관리자 상품 등록/수정 | Admin Service가 이 서비스의 관리자 전용 write API를 호출 |
| AD-0103 | 영양성분 등록 | `products`의 calories/carbohydrate/sugars/protein/fat/sodium 컬럼 직접 수정 |
| AD-0104 | 원재료·알레르기 등록 | `products.ingredient_text` 수정 + `product_tags`(ALLERGEN) 갱신. 태그 자체가 아니라 "이 상품에 어떤 태그를 붙일지"만 이 서비스가 결정 |

## 참고 쿼리

```sql
-- 카테고리/알레르기 필터 검색 (PR-0101~0104)
SELECT p.product_id, p.product_name, p.brand_name, p.image_url
FROM service.products p
JOIN service.product_tags pt_cat ON pt_cat.product_id = p.product_id
JOIN service.tags t_cat ON t_cat.tag_id = pt_cat.tag_id AND t_cat.tag_type = 'CATEGORY' AND t_cat.tag_code = $1
WHERE p.publish_status = 'ACTIVE'
  AND NOT EXISTS (
    SELECT 1 FROM service.product_tags pt_allergen
    JOIN service.tags t_allergen ON t_allergen.tag_id = pt_allergen.tag_id
    WHERE pt_allergen.product_id = p.product_id
      AND t_allergen.tag_type = 'ALLERGEN'
      AND t_allergen.tag_code = ANY($2::text[])  -- 사용자가 피하려는 알레르기 코드 목록
  );
```

## 미해결 항목

- 상품 리뷰(PR-0306)는 스키마에 없다. `service.product_reviews(review_id, product_id, user_id, rating, content, created_at)` 형태의 신규 테이블 설계가 필요하다.
