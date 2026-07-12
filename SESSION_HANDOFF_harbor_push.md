# 세션 핸드오프 — Harbor 실연동 작업 (2026-07-09 ~ 07-12)

> 이 문서는 노트북 로컬 환경(원격 데스크탑 아님)에서 Claude Code로 작업을 이어가기 위한
> 컨텍스트 손실 방지용 요약이다. 새 세션에서 이 파일을 함께 참조해서 작업을 이어가면 된다.

## 0. 협업 규칙 (메모리 미동기화 대비 — 반드시 새 세션에 이 규칙들을 적용할 것)

- **매 명령/도구 호출 전에 한 줄로 무엇을/왜/어떻게 할 건지 설명**한 뒤 실행할 것 (사소한 명령도 예외 없음)
- 텍스트 에디터가 필요하면 **nano 대신 vi** 사용
- 공식 문서를 근거로 제시할 때는 **최신 버전 문서를 실제 확인**하고 인용할 것 (확인 안 했으면 라벨링)
- **설계 판단이 필요한 작업**(아키텍처 트레이드오프, 보안 설계 등) 시작 전, 또는 작업 성격이
  라이브 인시던트 대응처럼 바뀔 때마다 **effort/모델 상향이 필요한지 계속 재평가하고 먼저 말할 것**
  (일회성 판단 아님, 매번 체크)
- 팀원과 공유해야 할 변경(공유 설정 파일, GitHub Secrets, main 병합 등)이 생기면 **먼저 알려줄 것**
- **되돌리기 어려운 작업(권한 변경, 볼륨 삭제 등) 전엔 부작용을 충분히 따져보고, 추측성 수정보다
  공식 도구/절차(예: Harbor의 `prepare` 스크립트)를 우선할 것** — 이번 세션에서 `chown -R`을
  섣불리 제안했다가 컨테이너를 깨뜨린 실수가 있었음, 같은 패턴 반복 금지

## 1. 프로젝트 배경

- **ZeroCheck**: 건강식품 라벨 OCR+AI 검증 웹서비스, 부트캠프 하이브리드 클라우드+온프레미스 인프라 수업 프로젝트
- 사용자(김지훈): Team Alpha SecOps + CI/CD 담당
- 개인 마감 7/20, Docker Compose 배포 7/22, k8s 7/23+
- 원칙: **돈 나가는 건 AWS 단계 이후부터** (그 전엔 무료/이미 보유한 자원만 사용)
- GitHub 저장소: `https://github.com/love-1006/zero` (Collaborator 권한 있음)
- 인프라: Proxmox 호스트(`k8s`, 192.168.0.10) 위에 VM 5대, 데스크탑 한 대(32GB RAM)를 나눠 씀
  - harbor VM: VMID 100, IP `192.168.0.53`, hostname `harbor`, SSH 계정 `bruce`, 스펙 8GB RAM/4코어
  - harbor-template: VMID 101 (미사용, 팀원 배포용 템플릿)

## 2. 완료된 것 (main에 병합됨)

- Git 저장소 + GitHub Flow 브랜치 전략 (`Jhoon/ci-cd/*`, `Jhoon/secops/*`, main에서만 분기·병합)
- gitleaks pre-commit 훅 (`.pre-commit-config.yaml`, `scripts/setup-hooks.sh`)
- GitHub Actions Lint 워크플로 (`.github/workflows/lint.yml`) — shellcheck+yamllint
- `.gitattributes` (라인엔딩 정규화), `.yamllint.yml`
- Build & Test 파이프라인 스켈레톤 — 임시 FastAPI 샘플(`ci_sandbox/`)로 검증 완료

## 3. 진행 중 — `Jhoon/ci-cd/harbor-push` 브랜치 (origin에 push됨)

### 커밋된 파일
- `Dockerfile`, `.dockerignore` — `ci_sandbox` 앱 이미지 빌드용
- `ci_sandbox/requirements.txt`에 `uvicorn[standard]` 추가
- `infra/sonarqube/docker-compose.yml`, `.env.example`, `README.md` — SonarQube Community 자체 호스팅용
- `.github/workflows/build-test.yml` — Job 분리 완료:
  - `build-test`: `runs-on: ubuntu-latest` (클라우드, 내부망 불필요)
  - `code-scanning`, `image-scanning`, `image-push`: `runs-on: self-hosted` (harbor VM, 내부망 필요)

### 핵심 아키텍처 결정 (이유 포함, 재논의 불필요)

1. **self-hosted runner가 harbor VM에 필요한 이유**: Harbor가 사설 IP(192.168.0.53)에 있어서
   GitHub 호스팅 클라우드 러너가 도달 불가. 단, self-hosted runner는 **아웃바운드 HTTPS만
   필요**(공식 문서 확인함)해서 harbor VM을 인터넷에 노출시킬 필요는 없음.
2. **러너 배치 위치**: harbor VM에 직접 (별도 VM 안 만듦) — 사용자의 원래 설계도(Proxmox 박스 안에
   Harbor+Trivy+SonarQube+CI/CD 다 포함)와 일치, 실측 리소스로도 충분 확인됨.
3. **Jenkins 대신 GitHub Actions 유지**: Jenkins도 결국 내부망 접근 가능한 컴퓨트가 필요해서
   근본 문제가 안 없어지고, 웹훅 방식이면 오히려 인바운드 노출이 필요해져 더 불리함.
4. **SonarCloud 대신 SonarQube 자체 호스팅**: SonarCloud 무료 티어(5만 LoC 제한)를 넘으면
   원치 않는 시점에 유료 전환 강요당할 리스크 있음 → "AWS 전까지 무비용" 원칙과 충돌 →
   자체 호스팅(라이선스 무료, 무제한)으로 결정.
5. **Job 분리(cloud/self-hosted)**: 내부망 필요 없는 checkout/pytest는 클라우드 러너로 보내
   harbor VM 부하 최소화. docker build/Trivy scan/Harbor push만 self-hosted에서 실행.
6. **VM 스펙(8GB/4코어) 유지, 증설 안 함**: 데스크탑 32GB를 VM 5대가 나눠 쓰는 상황이라 여유
   없음. 실측 결과 Harbor 전체 스택이 1GB 미만 사용 중이라 SonarQube 추가해도 문제 없음 확인.
7. **Harbor 내장 Trivy(`--with-trivy`)와 CI의 pre-push Trivy는 별개** — 둘 다 사용(이중 방어선).

## 4. 현재 라이브 이슈 — 진행 중인 트러블슈팅 (미해결, 여기서부터 이어가야 함)

### 타임라인
1. bruce 계정 비밀번호를 잊어버림 (기존 알려진 임시값 `test1234`도 안 먹힘)
2. **Proxmox 콘솔 → GRUB 복구모드(`init=/bin/bash`)로 비밀번호 재설정** — 이 과정에서 VM 재부팅 발생
3. 재부팅 후 **Harbor 핵심 컨테이너 전체(nginx, harbor-core, registry, registryctl, redis,
   harbor-db, jobservice, harbor-portal)가 자동으로 안 돌아옴** (`Exited (128)`, `harbor-log`만 생존)
   → **재부팅 시 자동 기동이 안 되는 근본 문제 발견, 아직 안 고침**
4. 복구 시도: `~/harbor`에서 `docker compose up -d` → `permission denied
   (/home/bruce/harbor/common/config/db/env)` 에러 (Harbor 설치 스크립트가 원래 root로
   실행되어 파일이 root 전용 권한이었음)
5. **실수**: `sudo chown -R bruce:bruce ~/harbor`로 전체 소유권 변경 → 일시적으로 compose는
   실행됐으나 **컨테이너 내부 프로세스가 기대하는 소유권 체계가 깨져서** registryctl/nginx/등이
   `permission denied` (예: `/etc/registryctl/config.yml`)로 재시작 루프에 빠짐
6. **올바른 복구**: `docker compose down` → `sudo ./prepare` (Harbor 공식 설정 재생성 스크립트,
   모든 `common/config/*` 파일을 올바른 내부 권한으로 재생성) → `sudo docker compose up -d`
   → **전체 컨테이너 healthy로 복구 완료**, 외부에서 443 포트 응답 확인함(`Test-NetConnection` 성공)
7. **현재 막힌 지점**: **Harbor admin 로그인 계정/비밀번호를 모름.**
   - `admin`/`admin` 시도 → 실패 (이건 SonarQube 계정이었음, 착오)
   - `admin`/`Harbor12345` 시도 (인수인계 문서의 최초 기본값) → 실패
   - 지금 `harbor.yml`의 `harbor_admin_password` 필드 값을 확인하려는 중
     (`grep harbor_admin_password ~/harbor/harbor.yml`) — **단, 이 값은 harbor-db가 최초
     초기화될 때만 반영되므로(43시간 전), 그 이후 UI로 비밀번호가 바뀌었으면 안 맞을 수 있음**

### 다음 세션에서 바로 이어갈 것
1. `grep harbor_admin_password ~/harbor/harbor.yml` 결과 확인, 그 값으로 로그인 재시도
2. 그래도 안 되면: Harbor 공식 문서의 "reset admin password" 절차 확인 필요
   (DB 직접 접근으로 admin 비밀번호 해시를 리셋하는 공식 방법이 있는지 검색 필요 — 아직 안 찾아봄)
3. 로그인 성공하면 **즉시 비밀번호 변경** (계속 미뤄진 보안 항목)

## 5. 로그인 성공 이후 남은 작업 (순서대로)

1. Harbor: `zerocheck` 프로젝트 생성 (Private)
2. Harbor: Robot Account 생성 — `zerocheck` 프로젝트 한정, **Push+Pull 권한만** (최소 권한).
   생성 시 표시되는 계정명/시크릿을 안전하게 보관 (`HARBOR_ROBOT_USER`/`HARBOR_ROBOT_TOKEN`으로 사용)
3. SonarQube(`http://192.168.0.53:9000`, 이미 healthy 상태로 떠있음): admin/admin 로그인 →
   비밀번호 변경 완료됨(`Zeropass123!`로 이미 변경함) → 토큰 발급도 이미 완료함(사용자가 보관 중,
   대화에 노출 안 시킴) → `SONAR_HOST_URL`로 쓸 주소 확인
4. GitHub 저장소(`love-1006/zero`) Settings에 등록:
   - Variables: `SONAR_HOST_URL` = `http://192.168.0.53:9000`
   - Secrets: `SONAR_TOKEN`, `HARBOR_ROBOT_USER`, `HARBOR_ROBOT_TOKEN`
5. **Harbor 재부팅 자동 기동 문제 근본 수정** — 아직 원인/해결 안 함. docker-compose의 restart
   정책 확인, 필요시 systemd 서비스 등록 등 검토 필요.
6. **bruce가 sudo 없이 안전하게 관리할 수 있는 방법** — `chown -R`은 실패한 접근이었음.
   docker 그룹 활용이나 범위 제한된 sudoers 규칙 등 컨테이너 내부 권한을 안 건드리는 대안 필요.
7. self-hosted GitHub Actions runner를 harbor VM에 설치 (GitHub 저장소 Settings → Actions →
   Runners → New self-hosted runner에서 나오는 실행 시점 등록 토큰 사용, **systemd 서비스로
   설치해서 재부팅 시 자동 기동되게 할 것**)
8. VM 쪽 별도 보안 항목(Claude Code 범위 밖, 여전히 미완료): bruce 계정 영구 비밀번호로 재변경
   (이번에 임시로 리셋한 값 말고 강한 값으로)

## 6. 아직 하나도 안 건드린 것

- Lane 2 (CD): `deploy trigger → docker pull → Docker Compose → SUCCESS/rollback`
  (`Jhoon/ci-cd/docker-deploy-pipeline` 브랜치, main과 미동기화)
- Rollback 커스텀 스크립트 (`Jhoon/ci-cd/rollback-config`)
- `.env` 템플릿 + pydantic Settings 표준 코드 (`Jhoon/secops/pydantic-settings`, `env-gitignore-template`)
