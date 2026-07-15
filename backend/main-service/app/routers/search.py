from fastapi import APIRouter

router = APIRouter()


@router.get("/search")
async def search_products(query: str, page: int, category: str | None = None, warning: str | None = None) -> dict[str, object]:
    # 상품 검색은 데이터팀이 관리하는 ElasticSearch 색인으로 제공될 예정(skill.md
    # 참고) — 아직 연동 전이라 "준비 중"만 내려준다. 연동되면 이 return문만 실제
    # 검색 호출로 바꾸면 된다. 요청 파라미터와 응답 스키마(results의
    # id/name/desc/url)는 기능명세서 API-Spec(MN-0102)과 이미 맞춰뒀다.
    return {"status": "PREPARING", "results": []}
