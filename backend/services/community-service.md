# Community Service

## 소유 데이터

`service-db-v1.0`에는 공지사항/게시글/좋아요 테이블이 **전혀 없다**. 신규 테이블 설계가 필요하다. 최소 골격 예시:

```sql
-- 예시 — 실제 컬럼/제약은 팀에서 확정
CREATE TABLE community.notices (
  notice_id UUID PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  thumbnail_url TEXT,
  hashtag VARCHAR(255),
  author_user_id INTEGER NOT NULL, -- public.users(id) 소프트 참조, DB FK는 스키마 분리 여부에 따라 선택
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE community.notice_likes (
  notice_id UUID NOT NULL REFERENCES community.notices(notice_id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (notice_id, user_id)
);
```

`author_user_id`/`user_id`를 실제 DB FK로 `public.users(id)`에 걸지, 소프트 참조로만 둘지는 Community Service가 User/Auth와 같은 DB를 쓰는지에 달려 있다. 같은 `test_db` 안이면 FK를 걸 수 있다(지금 이 저장소가 `user_health_profiles` 등에서 하는 것과 동일한 패턴).

## 참조하는 외부 데이터 (읽기 전용)

- `service.tags` (Ingredients Service 소유, `tag_type='SWEETENER'`) — CM-0107/0108 "감미료 정보" 화면은 새 테이블을 만들 필요 없이 **Ingredients Service의 기존 데이터를 그대로 재사용**하면 된다.

## 담당 기능 (기능명세서 기준)

| 기능ID | 설명 | 참고 |
|---|---|---|
| CM-0101~0105 | 공지사항 목록/본문/쓰기/수정/삭제 | 신규 `notices` 테이블 |
| CM-0106 | 좋아요 | 신규 `notice_likes` 테이블 |
| CM-0107~0108 | 감미료 목록/상세 | **자체 테이블 불필요** — Ingredients Service `tags` 그대로 사용 (`docs/services/ingredients-service.md` 참고) |

## 설계 시 참고

- 공지사항 작성/수정 권한은 Admin Service를 통해서만 열어주는 게 자연스럽다(SC-0102 관리자 권한 분리와 일치).
- CM-0102 "뉴스 링크로 이동"은 외부 URL로 리다이렉트하는 케이스도 있어 보이므로, `content`와 별개로 `external_url` 컬럼이 필요할 수 있다.
