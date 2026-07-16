# Diet Service (제로식단)

## 소유 데이터

- `service.meal_logs` (PK `meal_log_id` UUID, FK `user_id` → `public.users(id)`)
- `service.meal_items` (PK `meal_item_id` UUID, FK `meal_log_id` → `meal_logs`, FK `product_id` → `service.products`(nullable))
- view `service.v_meal_totals` (meal_log 단위 칼로리/당류/탄수화물 합계)
- `service.user_favorites`도 잠정적으로 이 서비스가 관리(아래 "미정 항목" 참고)

## 참조하는 외부 데이터 (읽기 전용)

- `public.users(id)` — JWT에서 나온 `user_id`를 그대로 사용, User/Auth 서비스에 별도 조회 불필요
- `service.products` — 식단에 상품을 추가할 때 이름/영양정보를 **스냅샷으로 복사**해서 `meal_items`에 저장(아래 참고)

## 핵심 설계: 이력 스냅샷

`meal_items`는 상품이 나중에 바뀌어도 과거 기록이 변하지 않도록 `item_name`/`calories`/`sugars`/`carbohydrate`를 섭취 당시 값으로 **복제 저장**한다. 즉:

- 식단에 상품 추가 시: `service.products`에서 현재 값을 읽어와 `meal_items`에 그대로 insert (참조가 아니라 복사)
- `product_id`는 "원본이 어떤 상품이었는지" 링크용일 뿐, 표시할 영양값은 항상 `meal_items` 자체 컬럼에서 읽는다
- 원본 상품이 삭제되면 `product_id`는 `ON DELETE SET NULL`로 NULL이 되지만 스냅샷 값은 그대로 남는다

## 레시피 참조는 느슨하다

`meal_items.external_recipe_id`(VARCHAR)는 Recipe Service의 레시피 ID를 문자열로만 들고 있고 **DB FK가 없다**. 레시피 존재 여부 확인이 필요하면 Recipe Service API를 호출해야 한다. `product_id`와 `external_recipe_id`는 동시에 채워질 수 없다(CHECK 제약).

## 담당 기능 (기능명세서 기준)

| 기능ID | 설명 | 참고 |
|---|---|---|
| RC-0101~0102 | 한끼/하루 식단 사진 업로드 | `meal_logs` insert (`input_type='VISION'`, `analysis_status='PENDING'`) |
| RC-0103~0104 | AI/OCR 분석 결과로 식단 항목 채우기 | 분석 완료 후 `meal_items` insert, `meal_logs.analysis_status='COMPLETED'`로 갱신 |
| RC-0105 | 대체 제품 추천 | Product Service 검색 API 호출(이 서비스 데이터 아님) |
| RC-0106 | 캘린더 (날짜별 식단) | `meal_logs.eaten_at` 기준 조회 |
| MN-0106~0108 | 홈 당/칼로리 게이지 | `v_meal_totals`를 하루 단위로 재집계 |

## 참고 쿼리

```sql
-- 하루 칼로리/당 합계 (MN-0106~0108). v_meal_totals는 meal_log 단위라 애플리케이션에서 하루로 묶는다.
SELECT date_trunc('day', ml.eaten_at) AS day,
       sum(vt.total_calories) AS calories,
       sum(vt.total_sugars) AS sugars
FROM service.meal_logs ml
JOIN service.v_meal_totals vt ON vt.meal_log_id = ml.meal_log_id
WHERE ml.user_id = $1 AND ml.eaten_at >= $2 AND ml.eaten_at < $3
GROUP BY 1;

-- 캘린더 (RC-0106)
SELECT meal_log_id, eaten_at, meal_type
FROM service.meal_logs
WHERE user_id = $1 AND eaten_at >= $2 AND eaten_at < $3
ORDER BY eaten_at;
```

## 미정 항목

- `user_favorites`(즐겨찾기)를 이 서비스가 가질지, User 쪽에 둘지 팀 결정이 필요하다. `product_id`(Product 도메인)와 `external_recipe_id`(Recipe 도메인)를 동시에 다루는 경계 테이블이라 어느 쪽이 맡아도 다른 한쪽에 대한 소프트 참조가 생긴다.
