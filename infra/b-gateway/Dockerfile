# openresty/openresty 공식 이미지는 non-root 실행을 아직 지원하지 않는다
# (openresty/docker-openresty#24, #119 - 업스트림에 미해결로 남은 이슈, nginx
# 공식 이미지의 nginx-unprivileged 같은 공식 변형이 openresty엔 없음). 커뮤니티에
# 문서화된 우회 패턴(pid/temp_path를 쓰기 가능한 경로로 재지정 + 전용 계정)을
# 그대로 따른다 - nginx 공식 문서(hub.docker.com/_/nginx "Running as a Non-Root
# User" 섹션)에 나열된 것과 동일한 경로 목록.
#
# 2026-07-19, well-architected 체크리스트 재점검 - b-gateway가 dangdang-edge에
# 직접 노출된 유일한 컴포넌트인데 root로 떠있던 걸 발견. backend 8개 서비스는
# 이미 전부 non-root라 이 게이트웨이만 예외였음. 이 Dockerfile은 격리된 환경에서
# 먼저 검증만 하고, production 적용은 별도 승인 후 진행한다(어제 이 파일에서
# 라이브 전환 중 버그 2개를 실제로 겪은 전례가 있어 신중하게 접근).
FROM openresty/openresty:alpine

RUN addgroup -g 101 -S nginx \
  && adduser -u 101 -D -S -G nginx nginx

COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf

USER nginx

EXPOSE 8080
