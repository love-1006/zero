# Main Service (메인화면)

## 소유 데이터 (잠정)

- `service.user_health_profiles` (PK `user_id` INTEGER → `public.users(id)`)
- `service.user_preferences` (PK `preference_id` UUID, FK `user_id` → `public.users(id)`, FK `tag_id` → `service.tags`)

> **이 배정은 확정이 아니다.** 7개 서비스 목록에 별도 "User/Profile Service"가 없어서 잠정적으로 Main에 붙였다. 팀에서 별도 서비스로 뺄지 결정 필요 — `docs/services/README.md`의 "열린 이슈" 참고. 또한 실제 `public.users`에 이미 `favorite_categories`/`is_allergic`/`tall`/`weight` 컬럼이 있어 이 두 테이블과 데이터가 겹칠 수 있다 — User/Auth 팀과 조율 전에는 신중하게 접근.

기본적으로 Main Service는 **자체 데이터를 최소화하고 다른 서비스를 조합하는 BFF**로 설계하는 게 맞다.

## 참조하는 외부 데이터 (읽기 전용, 전부 다른 서비스 호출/조합)

| 홈 화면 섹션 | 기능ID | 데이터 출처 |
|---|---|---|
| 통합 검색 | MN-0102 | Product Service |
| 당/칼로리 게이지 | MN-0106~0108 | Diet Service (`v_meal_totals` 집계) + 이 서비스의 `user_health_profiles.daily_*_target` |
| 사용자 맞춤 추천 | MN-0109 | Product Service (선호 카테고리는 `user_preferences` 기준으로 이 서비스가 필터 조건만 만들어 전달) |
| 인기 상품 랭킹 | MN-0110 | Product Service |
| 커뮤니티 인기글 | (구 기능명세 MN-0106, 최신본엔 없음) | Community Service |
| 인기 레시피 | (구 기능명세 MN-0107) | Recipe Service |
| AI 챗봇 / OCR 검색 | MN-0111~0113 | AI 분석 파이프라인 + Product Service 검색 |
| 마이페이지 관심분야/알레르기 설정 | US-0104~0106 | 이 서비스가 `user_preferences`/`user_health_profiles`에 직접 write |

## 참고 쿼리

```sql
-- 사용자 하루 목표 대비 섭취량 (MN-0106~0108). 목표는 Main이 갖고, 실섭취 합계는 Diet Service API/뷰에서 가져온다.
SELECT daily_calorie_target, daily_sugar_target_g
FROM service.user_health_profiles
WHERE user_id = $1;

-- 관심 카테고리 설정 저장 (US-0104)
INSERT INTO service.user_preferences (preference_id, user_id, preference_type, tag_id, created_at)
VALUES (gen_random_uuid(), $1, 'INTEREST_CATEGORY', $2, now())
ON CONFLICT DO NOTHING; -- uq_preferences_tag 부분 유니크 인덱스가 중복을 막아준다

-- 알레르기 설정 저장 (US-0105) — CAUTION_INGREDIENT는 tag_id 대신 custom_value를 쓴다는 점 주의
INSERT INTO service.user_preferences (preference_id, user_id, preference_type, tag_id, created_at)
VALUES (gen_random_uuid(), $1, 'ALLERGEN', $2, now());
```

## 주의

- `user_preferences`는 `preference_type`에 따라 `tag_id` 또는 `custom_value` 중 **정확히 하나만** 채워야 한다(CHECK 제약, `ck_preferences_value`). `INTEREST_CATEGORY`/`ALLERGEN`은 반드시 `tag_id`, `CAUTION_INGREDIENT`는 반드시 `custom_value`다.
- 홈 화면이 여러 서비스를 동시에 호출하는 구조이므로, 한 서비스가 느려도 전체 홈이 멈추지 않도록 타임아웃/부분 실패 허용(예: 인기글 로딩 실패해도 검색은 정상 노출) 설계를 권장한다.
