# Ingredients Service

## 소유 데이터

- `service.tags` (8컬럼, PK `tag_id` UUID, UNIQUE `(tag_type, tag_code)`)
  - `tag_type`: `CATEGORY` | `ALLERGEN` | `SWEETENER` | `HEALTH_LABEL`

쓰기(태그 신설/설명 수정/비활성화)는 이 서비스만 한다.

## 참조하는 외부 데이터 (읽기 전용)

- `service.product_tags` — 특정 태그가 몇 개 상품에 붙어있는지 집계할 때만 조회. 쓰지 않는다(Product Service 소유).

## 이 서비스가 신경 쓰지 않아도 되는 것

- CATEGORY 개수 검증 트리거(`ctr_product_category_after_tag`)는 `product_tags`에도 걸려 있지만, 트리거 로직 자체는 Product Service 도메인 규칙("상품은 카테고리가 정확히 1개")이다. Ingredients Service는 `tags` 원본만 정확히 유지하면 된다.
- 태그를 `active=false`로 비활성화해도 기존 `product_tags` 연결은 그대로 남는다(RESTRICT 정책 — 참조 중인 태그는 삭제 불가, 비활성화만 가능).

## 담당 기능 (기능명세서 기준)

| 기능ID | 설명 | 참고 |
|---|---|---|
| CM-0107 | 감미료 목록 | `SELECT * FROM service.tags WHERE tag_type='SWEETENER' AND active` |
| CM-0108 | 감미료 상세 | `tag_id`로 `description`/`caution_text`/`source_url` 반환 |
| PR-0104 | 주의 성분 필터용 알레르기 코드 목록 | `tag_type='ALLERGEN'` 목록을 Product Service가 필터 UI 구성에 사용하도록 노출 |
| AD-0104 (일부) | 원재료/알레르기 태그 마스터 관리 | 새 알레르기 유형·감미료 유형 추가·설명 수정 |

## 참고 쿼리

```sql
-- 태그 타입별 목록 (CM-0107, 필터 옵션 등)
SELECT tag_id, tag_code, tag_name, description
FROM service.tags
WHERE tag_type = $1 AND active = true
ORDER BY tag_name;

-- 태그 상세 + 연결된 상품 수 (관리자 화면용)
SELECT t.tag_id, t.tag_name, t.description, t.caution_text, t.source_url,
       (SELECT count(*) FROM service.product_tags pt WHERE pt.tag_id = t.tag_id) AS product_count
FROM service.tags t
WHERE t.tag_id = $1;
```

## 다른 서비스와의 경계

- Product/Community/Main 서비스는 `tags`를 **읽기 전용**으로만 참조한다. 검색 지연시간이 문제되면, Product Service 쪽에 태그 이름/설명을 캐시(주기 동기화)하는 방안을 고려하되 원본은 항상 이 서비스가 갖는다.
- `tags` 삭제/타입 변경은 `product_tags`, `user_preferences`(선호/알레르기 설정) 양쪽에 영향을 준다 — 변경 전 두 서비스에 통지할 방법(이벤트 발행 등)이 필요하다.
