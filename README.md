# OpenImpact

## 소개
OpenImpact는 취미 프로젝트로 개발되고 있는 오픈소스 프로젝트입니다.

## 비전
OpenImpact는 한국 연구자들을 위한 포괄적인 연구 지원 플랫폼을 지향합니다. 우리는 다음과 같은 목표를 가지고 있습니다:

### 연구 접근성 향상
- 다국어 논문 요약 및 번역 지원
- arxiv를 포함한 공개 논문들의 체계적 분류 및 통계 제공
- 연구 분야별 트렌드 분석 및 시각화

### 연구 생산성 향상
- 웹 기반 논문 작성 지원 도구 제공
- 다중 논문 분석 및 참조 인터페이스
- 맞춤형 Research Agent 개발 및 테스트 환경

### 연구 커뮤니티 활성화
- 언어 장벽 없는 연구 자료 접근
- LLM 기반 연구 지원 도구의 무료 제공
- 연구 질문, 방법론, 실험 결과의 개방적 공유
- 논문 데이터의 언어 모델 학습 활용 지원

## 주의사항
- 이 프로젝트는 외부 API를 사용하며, API 사용량에 따른 비용이 발생할 수 있습니다.
- API 비용 지원을 위한 기부는 언제나 환영합니다.

## 기여하기
- 이 프로젝트는 오픈소스이며, 여러분의 기여를 환영합니다.
- 버그 리포트, 기능 제안, 코드 기여 등 모든 형태의 기여가 가능합니다.
- 기여하시기 전에 [기여 가이드라인](CONTRIBUTING.md)을 확인해 주세요.

## 개발 환경 실행

### 백엔드
필요한 패키지 설치:
```bash
pip install fastapi uvicorn
```

프로젝트 루트에서 실행:
```bash
uvicorn services.web.backend.main:app --reload --port 8000
```

### 프론트엔드
프로젝트 루트에서 실행:
```bash
python -m http.server 3000 --directory services/web/frontend
```

### 접속 주소
- 프론트엔드: http://localhost:3000
- 백엔드: http://localhost:8000
- API 문서: http://localhost:8000/docs

## Contributors
<a href="https://github.com/hist0613/OpenImpact/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=hist0613/OpenImpact" />
</a>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=hist0613/OpenImpact&type=Date)](https://star-history.com/#hist0613/OpenImpact&Date)