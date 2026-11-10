# 비밀키 관리 정책 (Secrets Policy)

> M0 산출물 · 설계 `07-infrastructure.md §3`, `12-deployment-plan.md §2` 기반

## 원칙
1. **서버 전용 비밀**은 **GitHub Actions Secret**(암호화·로그 자동 마스킹)에만 저장한다. 코드·빌드 산출물·브라우저에 절대 포함하지 않는다.
2. **클라이언트 공개 변수**(anon, VAPID 공개키, URL)만 웹 빌드에 포함한다. 접근 통제는 **RLS**가 담당한다.
3. 로컬 개발은 루트 `.env`(gitignore) 사용. `.env.example`에는 **이름만**, 값 없음.
4. 어떤 서비스도 **결제 수단을 등록하지 않는다**. 유료 폴백 코드를 작성하지 않는다.

## 분류

| 변수 | 분류 | 저장 위치 |
|---|---|---|
| `SUPABASE_SERVICE_ROLE_KEY` | 🔴 서버 전용 | Actions Secret |
| `GEMINI_API_KEY` | 🔴 서버 전용 | Actions Secret |
| `VAPID_PRIVATE_KEY` | 🔴 서버 전용 | Actions Secret |
| `VAPID_SUBJECT` | 🔴 서버 전용 | Actions Secret |
| `DATA_GO_KR_KEY` | 🔴 서버 전용(선택) | Actions Secret |
| `VITE_SUPABASE_URL` / `SUPABASE_URL` | 🟢 공개 가능 | 빌드 변수 |
| `VITE_SUPABASE_ANON_KEY` | 🟢 공개 가능(RLS 전제) | 빌드 변수 |
| `VITE_VAPID_PUBLIC_KEY` | 🟢 공개 가능 | 빌드 변수 |

## 노출 방지 체크 (배포 전 필수, AC-8 / O-4)
- 웹 빌드 산출물(`apps/web/dist`)에 `SERVICE_ROLE` / `GEMINI` / `VAPID_PRIVATE` 문자열이 **없어야** 한다.
- `.gitignore`가 `.env*`(단, `.env.example` 제외)·`*.pem`·`*.key`를 포함한다.
- 커밋 전 `git diff --staged`로 비밀 유입 여부 확인.
