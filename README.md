# 🏭 공정 순서 기반 배치 최적화 시스템

Factory Mass Layout Algorithm을 기반으로 `main_process_sequence` 순서에 따라 공장 배치를 최적화하는 시스템입니다.

## 🎯 주요 특징

- **순서 준수**: 주공정의 `main_process_sequence` 순서를 엄격히 준수
- **전수 탐색**: 모든 가능한 회전/방향 조합을 체계적으로 탐색
- **다차원 적합도**: SLP 가중치, 유해인자, 부지 활용률 등을 종합 평가
- **실시간 시각화**: 최적화 진행 과정을 실시간으로 모니터링
- **결과 비교**: 상위 4개 솔루션은 크게, 나머지는 작게 표시하여 비교 분석

## 📁 프로젝트 구조

```
process_sequence_optimizer/
├── main_process_optimizer.py           # 메인 실행 스크립트
├── core/                               # 핵심 모듈
│   ├── __init__.py
│   ├── config_loader.py                # JSON 설정 파일 로더
│   ├── process_classifier.py           # 주/부공정 분류기
│   ├── layout_generator.py             # 순서 기반 배치 생성기
│   ├── fitness_calculator.py           # 적합도 계산기
│   └── constraint_handler.py           # 제약 조건 처리기
├── optimization/                       # 최적화 엔진
│   ├── __init__.py
│   ├── base_engine.py                  # 추상 기본 클래스
│   └── exhaustive_search.py            # 전수 탐색 최적화
├── visualization/                      # 시각화 모듈
│   ├── __init__.py
│   ├── realtime_visualizer.py          # 실시간 시각화
│   └── result_visualizer.py            # 결과 시각화
├── utils/                              # 유틸리티
│   ├── __init__.py
│   └── geometry_utils.py               # 기하학적 유틸리티
├── requirements.txt                    # 필요 라이브러리
└── README.md                          # 프로젝트 설명서
```

## 🚀 설치 및 실행

### 1. 필수 라이브러리 설치

```bash
# 최소 요구사항 (핵심 기능만)
pip install numpy matplotlib

# 또는 전체 개발 환경
pip install -r requirements.txt
```

### 2. 설정 파일 준비

JSON 형태의 설정 파일이 필요합니다:

```json
{
    "site_dimensions": {
        "width": 25,
        "height": 15
    },
    "spaces": {
        "process_a": {
            "width": 4,
            "height": 3,
            "building_type": "main",
            "main_process_sequence": 1,
            "name": "공정 A"
        },
        "process_b": {
            "width": 5,
            "height": 3.5,
            "building_type": "main",
            "main_process_sequence": 2,
            "name": "공정 B"
        },
        "warehouse": {
            "width": 3,
            "height": 2.5,
            "building_type": "sub",
            "name": "창고"
        }
    },
    "adjacency_weights": {
        "process_a-process_b": {
            "weight": 10,
            "preferred_gap": 1.5
        }
    }
}
```

### 3. 실행

```bash
# 대화형 모드 실행
python main_process_optimizer.py layout_config.json

# 또는 Python 스크립트에서
from main_process_optimizer import ProcessSequenceOptimizer

optimizer = ProcessSequenceOptimizer('layout_config.json')
solutions = optimizer.optimize(algorithm='exhaustive')
```

## 📊 설정 파일 구조

### 필수 설정

| 키 | 설명 | 예시 |
|---|---|---|
| `site_dimensions` | 부지 크기 (mm) | `{"width": 1000, "height": 800}` |
| `spaces` | 공정 정보 | 아래 참조 |

### spaces 설정 (공정별)

| 키 | 설명 | 필수 | 예시 |
|---|---|---|---|
| `width` | 공정 너비 (m) | ✅ | `4.5` |
| `height` | 공정 높이 (m) | ✅ | `3.0` |
| `building_type` | 공정 타입 | ✅ | `"main"`, `"sub"`, `"fixed"` |
| `main_process_sequence` | 주공정 순서 | main일 때 | `1`, `2`, `3`, ... |
| `name` | 공정 이름 | ❌ | `"공정 A"` |

### 선택적 설정

| 키 | 설명 | 예시 |
|---|---|---|
| `adjacency_weights` | SLP 인접성 가중치 | `{"A-B": {"weight": 10, "preferred_gap": 1.5}}` |
| `fixed_zones` | 고정 구역 (도로, 주차장 등) | `[{"x": 0, "y": 12, "width": 25, "height": 3}]` || 키 | 설명 | 예시 |
|---|---|---|
| `adjacency_weights` | SLP 인접성 가중치 | `{"A-B": {"weight": 10, "preferred_gap": 1.5}}` |
| `fixed_zones` | 고정 구역 (도로, 주차장 등) | `[{"x": 0, "y": 12, "width": 25, "height": 3}]` |
| `hazard_factors` | 유해인자 정보 | `{"process_a": ["화재", "폭발"]}` |

## 🎯 SLP 가중치 기준

| 코드 | 가중치 | 의미 | 설명 |
|---|---|---|---|
| A | 10 | Absolutely necessary | 절대적으로 필요 |
| E | 8 | Especially important | 특히 중요 |
| I | 6 | Important | 중요 |
| O | 4 | Ordinary closeness | 일반적 근접성 |
| U | 2 | Unimportant | 중요하지 않음 |
| X | 0 | Undesirable | 바람직하지 않음 |

## 🔧 최적화 알고리즘

### 전수 탐색 (Exhaustive Search)
- **특징**: 모든 가능한 조합을 체계적으로 탐색
- **장점**: 최적해 보장, 고품질 결과
- **단점**: 공정 수가 많으면 시간 오래 걸림
- **적용**: 8개 이하 공정에 권장

### 복잡도 분석
- 회전 조합: 2^n (n = 공정 수)
- 방향 조합: 4^(n-1)
- 총 조합 수: 2^n × 4^(n-1)

**예시:**
- 3개 공정: 128개 조합 (~1초)
- 4개 공정: 512개 조합 (~5초)  
- 5개 공정: 2,048개 조합 (~20초)
- 6개 공정: 8,192개 조합 (~1분)

## 📈 적합도 평가 기준

### 보너스 점수
- **인접성**: SLP 가중치 기반 배치 적절성
- **순서 준수**: 주공정 순서 및 연결성
- **부지 활용률**: 40-70%에서 최대 점수
- **컴팩트성**: 공정들의 집약적 배치
- **접근성**: 도로/출입구와의 거리

### 페널티
- **겹침**: 공정 간 중복 배치 (치명적)
- **경계 위반**: 부지 경계 벗어남 (치명적)
- **고정구역 침범**: 도로/주차장 등 침범 (치명적)
- **유해인자**: 안전 거리 미준수

## 🖼️ 시각화 기능

### 실시간 모니터링
- 최적화 진행률 표시
- 현재 최적 배치 실시간 업데이트
- 적합도 진화 과정 그래프
- 예상 소요 시간 계산

### 결과 표시
- **상위 4개**: 큰 화면으로 상세 표시
- **나머지 4개**: 작은 화면으로 요약 표시
- **상세 분석**: 개별 솔루션 심층 분석
- **비교 분석**: 솔루션 간 비교

## 📝 배치 코드 형식

생성된 배치는 다음과 같은 코드로 표현됩니다:

```
AO-b(1.5)-BR-c(2.0)-CO
```

**해석:**
- `AO`: 공정 A, 원본 방향 (0도)
- `b(1.5)`: 오른쪽 방향으로 1.5m 간격
- `BR`: 공정 B, 90도 회전
- `c(2.0)`: 위쪽 방향으로 2.0m 간격  
- `CO`: 공정 C, 원본 방향

**방향 코드:**
- `a`: 아래쪽 (bottom)
- `b`: 오른쪽 (right)
- `c`: 위쪽 (top)
- `d`: 왼쪽 (left)

## 🔍 사용 예제

### 기본 사용법

```python
from main_process_optimizer import ProcessSequenceOptimizer

# 1. 최적화기 초기화
optimizer = ProcessSequenceOptimizer('config.json')

# 2. 전수 탐색 실행
solutions = optimizer.optimize(
    algorithm='exhaustive',
    max_solutions=8
)

# 3. 결과 확인
if solutions:
    best = solutions[0]
    print(f"최고 적합도: {best['fitness']:.2f}")
    print(f"배치 코드: {best['code']}")
```

### 샘플 프로젝트 생성

```python
# 샘플 설정 파일 자동 생성
from core.config_loader import create_sample_config

create_sample_config('sample_config.json')
```

## ⚠️ 주의사항

1. **순서 번호**: `main_process_sequence`는 1부터 시작하여 연속되어야 함
2. **공정 크기**: 개별 공정이 부지 크기를 초과하면 안됨
3. **유해인자**: 안전 거리 요구사항을 준수해야 함 (m 단위)
4. **GUI 환경**: matplotlib GUI 백엔드가 없으면 콘솔 모드로 자동 전환
5. **단위**: 모든 거리/크기는 m(미터) 단위 사용

## 📏 단위 정보

- **부지 크기**: m (미터) 단위
- **공정 크기**: m (미터) 단위  
- **거리/간격**: m (미터) 단위
- **preferred_gap**: m (미터) 단위
- **유해인자 안전거리**: m (미터) 단위

## 🛠️ 개발 정보

- **언어**: Python 3.8+
- **주요 라이브러리**: NumPy, Matplotlib
- **단위 체계**: 국제 표준 m(미터) 단위
- **라이선스**: MIT
- **개발자**: Process Layout Optimization Team

## 📞 지원 및 문의

- 🐛 **버그 리포트**: Issues 섹션 활용
- 💡 **기능 제안**: Pull Request 환영
- 📚 **문서**: 코드 내 주석 및 docstring 참조

---

**🚀 지금 시작해보세요!**

```bash
git clone [repository-url]
cd process_sequence_optimizer
pip install numpy matplotlib
python create_test_config.py
python main_process_optimizer.py test_layout_config.json
```
| `hazard_factors` | 유해인자 정보 | `{"process_a": ["화재", "폭발"]}` |

## 🎯 SLP 가중치 기준

| 코드 | 가중치 | 의미 | 설명 |
|---|---|---|---|
| A | 10 | Absolutely necessary | 절대적으로 필요 |
| E | 8 | Especially important | 특히 중요 |
| I | 6 | Important | 중요 |
| O | 4 | Ordinary closeness | 일반적 근접성 |
| U | 2 | Unimportant | 중요하지 않음 |
| X | 0 | Undesirable | 바람직하지 않음 |

## 🔧 최적화 알고리즘

### 전수 탐색 (Exhaustive Search)
- **특징**: 모든 가능한 조합을 체계적으로 탐색
- **장점**: 최적해 보장, 고품질 결과
- **단점**: 공정 수가 많으면 시간 오래 걸림
- **적용**: 8개 이하 공정에 권장

### 복잡도 분석
- 회전 조합: 2^n (n = 공정 수)
- 방향 조합: 4^(n-1)
- 총 조합 수: 2^n × 4^(n-1)

**예시:**
- 3개 공정: 128개 조합 (~1초)
- 4개 공정: 512개 조합 (~5초)  
- 5개 공정: 2,048개 조합 (~20초)
- 6개 공정: 8,192개 조합 (~1분)

## 📈 적합도 평가 기준

### 보너스 점수
- **인접성**: SLP 가중치 기반 배치 적절성
- **순서 준수**: 주공정 순서 및 연결성
- **부지 활용률**: 40-70%에서 최대 점수
- **컴팩트성**: 공정들의 집약적 배치
- **접근성**: 도로/출입구와의 거리

### 페널티
- **겹침**: 공정 간 중복 배치 (치명적)
- **경계 위반**: 부지 경계 벗어남 (치명적)
- **고정구역 침범**: 도로/주차장 등 침범 (치명적)
- **유해인자**: 안전 거리 미준수

## 🖼️ 시각화 기능

### 실시간 모니터링
- 최적화 진행률 표시
- 현재 최적 배치 실시간 업데이트
- 적합도 진화 과정 그래프
- 예상 소요 시간 계산

### 결과 표시
- **상위 4개**: 큰 화면으로 상세 표시
- **나머지 4개**: 작은 화면으로 요약 표시
- **상세 분석**: 개별 솔루션 심층 분석
- **비교 분석**: 솔루션 간 비교

## 📝 배치 코드 형식

생성된 배치는 다음과 같은 코드로 표현됩니다:

```
AO-b(50)-BR-c(30)-CO
```

**해석:**
- `AO`: 공정 A, 원본 방향 (0도)
- `b(50)`: 오른쪽 방향으로 50mm 간격
- `BR`: 공정 B, 90도 회전
- `c(30)`: 위쪽 방향으로 30mm 간격  
- `CO`: 공정 C, 원본 방향

**방향 코드:**
- `a`: 아래쪽 (bottom)
- `b`: 오른쪽 (right)
- `c`: 위쪽 (top)
- `d`: 왼쪽 (left)

## 🔍 사용 예제

### 기본 사용법

```python
from main_process_optimizer import ProcessSequenceOptimizer

# 1. 최적화기 초기화
optimizer = ProcessSequenceOptimizer('config.json')

# 2. 전수 탐색 실행
solutions = optimizer.optimize(
    algorithm='exhaustive',
    max_solutions=8
)

# 3. 결과 확인
if solutions:
    best = solutions[0]
    print(f"최고 적합도: {best['fitness']:.2f}")
    print(f"배치 코드: {best['code']}")
```

### 샘플 프로젝트 생성

```python
# 샘플 설정 파일 자동 생성
from core.config_loader import create_sample_config

create_sample_config('sample_config.json')
```

## ⚠️ 주의사항

1. **순서 번호**: `main_process_sequence`는 1부터 시작하여 연속되어야 함
2. **공정 크기**: 개별 공정이 부지 크기를 초과하면 안됨
3. **유해인자**: 안전 거리 요구사항을 준수해야 함
4. **GUI 환경**: matplotlib GUI 백엔드가 없으면 콘솔 모드로 자동 전환

## 🛠️ 개발 정보

- **언어**: Python 3.8+
- **주요 라이브러리**: NumPy, Matplotlib
- **라이선스**: MIT
- **개발자**: Process Layout Optimization Team

## 📞 지원 및 문의

- 🐛 **버그 리포트**: Issues 섹션 활용
- 💡 **기능 제안**: Pull Request 환영
- 📚 **문서**: 코드 내 주석 및 docstring 참조

---

**🚀 지금 시작해보세요!**

```bash
git clone [repository-url]
cd process_sequence_optimizer
pip install numpy matplotlib
python main_process_optimizer.py sample_layout_config.json
```
