from fastapi import APIRouter

router = APIRouter(prefix="/home")


@router.get("/rank/item")
async def get_product_ranking() -> dict[str, object]:
    # 인기 랭킹(조회수/비교횟수)은 Kafka→MongoDB 분석 파이프라인 데이터라
    # (admin-service.md AD-0109~0112 참고) 이 서비스는 아직 그 파이프라인에
    # 연결돼 있지 않다 — "준비 중"만 내려준다. 연동되면 이 return문만 실제
    # 집계 호출로 바꾸면 된다. 응답 스키마(listProducts의
    # rank/name/brand/image/url)는 기능명세서 API-Spec(MN-0110)과 이미 맞춰뒀다.
    return {"status": "PREPARING", "listProducts": []}
