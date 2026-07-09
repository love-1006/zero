# ZeroCheck 인수인계 — Harbor TLS 완료 & Claude Code 전환

> 작성일: 2026-07-09
> 목적: web 대화(claude.ai)에서 Harbor TLS 구축을 완료했고, 이후 Git/CI/CD 코드 작업을 Claude Code(VS Code)에서 이어가기 위한 핸드오프.
> 이 문서를 Claude Code 작업 repo 루트에 두거나, 새 세션 첫 프롬프트에 붙여넣어 맥락을 이어받으세요.

---

## 1. 프로젝트 / 역할 컨텍스트

- **프로젝트**: ZeroCheck — 건강 관련 식품 표시(무설탕/제로/저칼로리 등)를 OCR+AI로 실제 영양성분과 대조 검증하는 웹 서비스
- **팀**: Team Alpha — 김성애(팀장, 프론트), 최윤경(부팀장, DB/스키마), 이재헌(백엔드), **김지훈(본인) — SecOps + CI/CD**
- **CI/CD 파이프라인 목표**: GitHub Actions → SonarQube → Trivy → Harbor
- **일정**: 개인 마감(SecOps+CI/CD) **7/20**, Docker Compose 1차 배포 **7/22**, 쿠버네티스 전환 **7/23 이후**

---

## 2. 오늘(7/9) 완료된 작업: Harbor TLS 구축 ✅

harbor VM(`bruce@192.168.0.53`, hostname 내부 `harbor`)에 Harbor를 TLS로 구축 완료. **HTTP 먼저 기동 검증 → TLS 적용** 순서 원칙을 지켜서 진행함.

### 완료 내역
- **Harbor 버전**: v2.15.1 (offline installer, `--with-trivy` 옵션으로 설치)
- **접속 이름**: `harbor.hizero.local` (`/etc/hosts`에 `192.168.0.53 harbor.hizero.local` 등록)
- **data_volume**: 기본값 `/data` (root 70GB 파티션 내. 부트캠프 단계엔 충분. 부족해지면 별도 디스크 추가 마운트가 표준 확장 방식 — 지금은 불필요)
- **TLS 인증서**: 자체서명 (사내망이라 Let's Encrypt 불가)
  - CA: `/data/cert/ca.key`, `/data/cert/ca.crt` (CN=HiZero Root CA)
  - 서버 인증서: `/data/cert/harbor.hizero.local.crt` / `.key`
  - **SAN 포함**: `DNS:harbor.hizero.local, IP Address:192.168.0.53` (요즘 Docker/브라우저는 SAN 필수)
  - 유효기간 3650일
- **Docker daemon 신뢰 설정**: `/etc/docker/certs.d/harbor.hizero.local/ca.crt` 배치 (CA 인증서를 넣어야 함, 서버 인증서 아님)
- **검증 완료**:
  - `curl -I https://harbor.hizero.local --cacert /data/cert/ca.crt` → 정상
  - `docker login harbor.hizero.local` → **Login Succeeded**
  - push/pull 테스트: `harbor.hizero.local/test/hello-world:v1` push/pull 모두 성공
  - 브라우저 https 웹 UI 접속 정상

### harbor.yml 핵심 설정 (최종 상태)
```
hostname: harbor.hizero.local
http:
  port: 80
https:
  port: 443
  certificate: /data/cert/harbor.hizero.local.crt
  private_key: /data/cert/harbor.hizero.local.key
data_volume: /data
harbor_admin_password: Harbor12345   # ⚠️ 아래 미완료 항목 참고
```

---

## 3. ⚠️ 아직 처리 안 된 즉시 항목 (보안 — 최우선)

> 이 두 개는 harbor VM에서 직접 처리해야 하는 것이고 Claude Code 작업과 별개. **미처리 상태이니 잊지 말 것.**

- [ ] **Harbor admin 비밀번호 변경**: 현재 기본값 `Harbor12345` 그대로. 웹 UI 우상단 admin → Change Password. 기본 자격증명 노출 상태라 SecOps상 반드시 변경.
- [ ] **bruce 계정 비밀번호 변경**: 트러블슈팅 중 임시로 `test1234`로 바뀐 상태. VM에서 `passwd`로 강한 비밀번호 재설정.

---

## 4. 다음 작업 (Claude Code에서 진행) — 우선순위 순

> 아래는 전부 **로컬 repo에서 파일 생성·수정·커밋하는 작업**이라 Claude Code(VS Code)가 적합. harbor VM 원격 작업이 아님.

### 4-1. Git 저장소 생성 + 브랜치 전략 확정
- GitHub Flow 기반, 이미 다이어그램으로 확정된 **5개 브랜치 구조**:
  - `Jhoon/ci-cd`
  - `Jhoon/secops`
  - `yoonK/database`
  - `Jheon/back`
  - `sungA/front`
- GitHub Flow 원칙: 모든 브랜치는 `main`에서 나오고 `main`으로만 머지, cross-lane 연결 없음.

### 4-2. SecOps: gitleaks pre-commit hook 설치 + 팀 배포
- gitleaks pre-commit hook 설치 스크립트 작성 → 팀 전체 배포 (secret 유출 방지 최우선)

### 4-3. GitHub Actions 기본 워크플로우 (lint)
- 기본 lint 워크플로우부터 구성

### 4-4. GitHub Actions ↔ SonarQube 연동
- SonarQube 설치 (인프라)
- GitHub Actions에서 SonarQube 연동, 정적분석 결과 확인
- **주의(확인된 사실)**: SonarQube Quality Gate 결과는 **비동기**. GitHub Actions에서 **폴링 설정** 필요.

### 4-5. Trivy 컨테이너 이미지 스캔
- **주의(확인된 사실)**: Trivy 기본값이 **exit-code 0**. 빌드를 실패시키려면 **severity threshold + exit-code 플래그를 명시**해야 함.

### 4-6. 시크릿 관리
- `.env` 템플릿 + 시크릿 관리 가이드 작성
- pydantic Settings 표준 코드 (안전한 시크릿 로딩)

### 4-7. (별도) CI/CD draw.io 다이어그램 Lane 2(CD) 마무리
- Lane 1(CI) 완성됨. Lane 2(CD)는 레인 교차 화살표 레이아웃 문제 미해결. (이건 draw.io 작업이라 Claude Code와 무관 — web 대화에서 이어가는 게 나음)

---

## 5. 확정된 인프라 현황

| 항목 | 값 |
|---|---|
| harbor VM (운영) | VMID 100, IP `192.168.0.53` (netplan static), MAC `bc:24:11:99:57:57`, hostname `harbor` |
| harbor 접속 이름 | `harbor.hizero.local` (hosts 등록 필요) |
| harbor-template | VMID 101, Proxmox template 상태 (팀원 배포용 + k8s 노드 베이스 겸용) |
| 기존 템플릿 | VMID 9000 `ubuntu-2404-template` (cloud-init 기반, 이번 작업 무관) |
| Proxmox 호스트 | 노드 `k8s`, `192.168.0.10` |
| OS | Ubuntu Server 24.04 LTS (noble) |
| Docker | Engine 29.6.1, Compose v5.3.1 |
| Harbor | v2.15.1, TLS 적용 완료, Trivy 포함 |
| SSH 계정 | `bruce` (비밀번호 `test1234` 임시값 — 재변경 필요) |

---

## 6. 다른 팀원/서버가 Harbor에 접속하려면 (참고)

Harbor에 push/pull하려는 모든 클라이언트(팀원 PC, 향후 k8s 노드 등)는 아래 2가지가 필요:
1. **hosts 등록**: `192.168.0.53 harbor.hizero.local`
   - Linux: `/etc/hosts` / Windows: `C:\Windows\System32\drivers\etc\hosts`
2. **CA 신뢰**: harbor VM의 `/data/cert/ca.crt`를 받아서
   - Docker: `/etc/docker/certs.d/harbor.hizero.local/ca.crt`에 배치
   - (Windows Docker Desktop은 경로/방식이 다름 — 필요시 그때 안내)

---

## 7. 작업 스타일 / 원칙 (Claude Code 세션에서도 유지)

- **검증 우선**: 미확인 주장을 확정 사실로 제시하지 말 것. 근거 라벨링 유지 — `[웹검색 검증]`, `[팀 확정 전제]`, `[팀 결정, 검증 근거 없음]`
- **한 번에 하나씩** 순차 진행. 한 항목 완료 후 다음으로.
- **성공 기준 먼저**: 코드 작성 시 검증 방법(테스트 케이스, 예상 출력)을 함께 요청/제시.
- harbor VM은 nano/vi 미사용 환경 → 파일 생성 시 `cat > 파일명 << 'EOF' ... EOF` heredoc 방식. (단, Claude Code 로컬 작업은 에디터 직접 편집이므로 이 제약은 VM 원격 작업에만 해당)
- 버튼형 UI보다 일반 대화형 질문 선호.

---

## 8. Claude Code 새 세션 시작 프롬프트 예시

> 아래를 Claude Code 첫 메시지로 쓰면 맥락을 빠르게 이어받을 수 있음:

```
ZeroCheck 프로젝트의 SecOps + CI/CD 담당이야. harbor VM(192.168.0.53)에
Harbor v2.15.1 TLS 구축은 이미 완료했고(harbor.hizero.local, docker login/push/pull
검증 끝남), 이제 로컬 repo에서 Git/CI/CD 코드 작업을 이어가려고 해.

첨부한 인수인계 문서(ZeroCheck_인수인계_ClaudeCode전환.md) 기준으로,
먼저 Git 저장소 초기화 + 5개 브랜치 전략(GitHub Flow) 세팅부터 시작하자.
브랜치: Jhoon/ci-cd, Jhoon/secops, yoonK/database, Jheon/back, sungA/front

검증 근거 라벨링([웹검색 검증] 등) 유지하고, 한 번에 하나씩 순차로 진행해줘.
```
