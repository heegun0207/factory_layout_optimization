"""
최적화 엔진 기본 클래스
모든 최적화 알고리즘이 상속받는 추상 기본 클래스입니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import time


class OptimizationEngine(ABC):
    """최적화 엔진 추상 기본 클래스"""
    
    def __init__(self, layout_generator, fitness_calculator, constraint_handler):
        """
        초기화
        
        Args:
            layout_generator: 배치 생성기
            fitness_calculator: 적합도 계산기
            constraint_handler: 제약 조건 처리기
        """
        self.layout_generator = layout_generator
        self.fitness_calculator = fitness_calculator
        self.constraint_handler = constraint_handler
        
        # 최적화 결과 저장
        self.best_solutions = []
        self.fitness_history = []
        self.optimization_history = []
        
        # 성능 측정
        self.start_time = None
        self.end_time = None
        
        # 알고리즘 이름 (하위 클래스에서 설정)
        self.name = "Base Optimization Engine"
    
    @abstractmethod
    def optimize(self, 
                main_processes: List[Dict[str, Any]], 
                sub_processes: List[Dict[str, Any]], 
                **kwargs) -> List[Dict[str, Any]]:
        """
        최적화 실행 - 각 알고리즘별로 구현 필요
        
        Args:
            main_processes: 주공정 목록
            sub_processes: 부공정 목록
            **kwargs: 알고리즘별 추가 파라미터
        
        Returns:
            최적화된 솔루션 목록
        """
        pass
    
    def evaluate_solution(self, layout: List[Dict[str, Any]]) -> float:
        """
        솔루션 평가 (제약 조건 + 적합도)
        
        Args:
            layout: 평가할 배치
        
        Returns:
            평가 점수 (제약 조건 위반시 음수)
        """
        # 제약 조건 검사
        if not self.constraint_handler.is_valid(layout):
            return float('-inf')
        
        # 적합도 계산
        return self.fitness_calculator.calculate_fitness(layout)
    
    def update_best_solutions(self, solution: Dict[str, Any], max_keep: int = 20):
        """
        베스트 솔루션 목록 업데이트
        
        Args:
            solution: 새로운 솔루션
            max_keep: 유지할 최대 솔루션 수
        """
        # 솔루션에 평가 시간 추가
        solution['evaluation_time'] = time.time()
        
        # 베스트 솔루션에 추가
        self.best_solutions.append(solution)
        
        # 적합도 순으로 정렬
        self.best_solutions.sort(key=lambda x: x['fitness'], reverse=True)
        
        # 상위 max_keep개만 유지
        if len(self.best_solutions) > max_keep:
            self.best_solutions = self.best_solutions[:max_keep]
        
        # 적합도 히스토리 업데이트
        self.fitness_history.append(solution['fitness'])
    
    def get_best_solution(self) -> Optional[Dict[str, Any]]:
        """최고 적합도 솔루션 반환"""
        return self.best_solutions[0] if self.best_solutions else None
    
    def get_solution_diversity(self) -> float:
        """
        솔루션 다양성 측정 (배치 코드 기반)
        
        Returns:
            다양성 지수 (0~1, 높을수록 다양)
        """
        if len(self.best_solutions) < 2:
            return 0.0
        
        codes = [solution.get('code', '') for solution in self.best_solutions]
        unique_codes = set(codes)
        
        return len(unique_codes) / len(codes)
    
    def get_convergence_info(self) -> Dict[str, Any]:
        """수렴 정보 분석"""
        
        if not self.fitness_history:
            return {'converged': False, 'message': '히스토리 없음'}
        
        # 최근 10%의 개선율 확인
        recent_portion = max(10, len(self.fitness_history) // 10)
        if len(self.fitness_history) < recent_portion:
            return {'converged': False, 'message': '데이터 부족'}
        
        recent_scores = self.fitness_history[-recent_portion:]
        improvement = (max(recent_scores) - min(recent_scores)) / max(recent_scores) if max(recent_scores) > 0 else 0
        
        convergence_info = {
            'converged': improvement < 0.01,  # 1% 미만 개선시 수렴
            'improvement_rate': improvement,
            'recent_best': max(recent_scores),
            'overall_best': max(self.fitness_history),
            'generations_analyzed': recent_portion,
            'total_generations': len(self.fitness_history)
        }
        
        if convergence_info['converged']:
            convergence_info['message'] = f"수렴 완료 (최근 {recent_portion}세대 개선율 {improvement:.1%})"
        else:
            convergence_info['message'] = f"수렴 중 (최근 {recent_portion}세대 개선율 {improvement:.1%})"
        
        return convergence_info
    
    def start_optimization(self):
        """최적화 시작 시간 기록"""
        self.start_time = time.time()
        self.best_solutions.clear()
        self.fitness_history.clear()
        self.optimization_history.clear()
    
    def end_optimization(self):
        """최적화 종료 시간 기록"""
        self.end_time = time.time()
    
    def get_optimization_time(self) -> float:
        """최적화 소요 시간 반환 (초)"""
        if self.start_time is None:
            return 0.0
        
        end_time = self.end_time if self.end_time else time.time()
        return end_time - self.start_time
    
    def record_optimization_step(self, step_info: Dict[str, Any]):
        """최적화 단계 기록"""
        step_info['timestamp'] = time.time()
        step_info['elapsed_time'] = self.get_optimization_time()
        self.optimization_history.append(step_info)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 지표 반환"""
        
        metrics = {
            'algorithm': self.name,
            'optimization_time': self.get_optimization_time(),
            'solutions_found': len(self.best_solutions),
            'evaluations_performed': len(self.fitness_history),
            'diversity': self.get_solution_diversity(),
            'convergence': self.get_convergence_info()
        }
        
        if self.fitness_history:
            metrics['fitness_statistics'] = {
                'best': max(self.fitness_history),
                'worst': min(self.fitness_history),
                'average': sum(self.fitness_history) / len(self.fitness_history),
                'final': self.fitness_history[-1] if self.fitness_history else 0
            }
        
        return metrics
    
    def compare_with_baseline(self, baseline_solution: Dict[str, Any]) -> Dict[str, Any]:
        """기준 솔루션과 비교"""
        
        best_solution = self.get_best_solution()
        if not best_solution:
            return {'error': '비교할 솔루션이 없습니다'}
        
        comparison = {
            'baseline_fitness': baseline_solution.get('fitness', 0),
            'optimized_fitness': best_solution['fitness'],
            'improvement': best_solution['fitness'] - baseline_solution.get('fitness', 0),
            'improvement_percent': 0,
            'is_better': best_solution['fitness'] > baseline_solution.get('fitness', 0)
        }
        
        if baseline_solution.get('fitness', 0) > 0:
            comparison['improvement_percent'] = (comparison['improvement'] / baseline_solution['fitness']) * 100
        
        return comparison
    
    def export_results(self) -> Dict[str, Any]:
        """결과 내보내기"""
        
        return {
            'algorithm_info': {
                'name': self.name,
                'optimization_time': self.get_optimization_time(),
                'timestamp': time.time()
            },
            'solutions': self.best_solutions,
            'fitness_history': self.fitness_history,
            'optimization_history': self.optimization_history,
            'performance_metrics': self.get_performance_metrics(),
            'convergence_info': self.get_convergence_info()
        }
    
    def print_summary(self):
        """최적화 결과 요약 출력"""
        
        metrics = self.get_performance_metrics()
        
        print(f"\n📊 {self.name} 결과 요약")
        print(f"=" * 50)
        print(f"⏱️  최적화 시간: {metrics['optimization_time']:.2f}초")
        print(f"🎯 발견된 솔루션: {metrics['solutions_found']}개")
        print(f"🔍 평가 횟수: {metrics['evaluations_performed']}회")
        print(f"🌈 솔루션 다양성: {metrics['diversity']:.2f}")
        
        if 'fitness_statistics' in metrics:
            fs = metrics['fitness_statistics']
            print(f"📈 적합도 통계:")
            print(f"   최고: {fs['best']:.2f}")
            print(f"   최저: {fs['worst']:.2f}")  
            print(f"   평균: {fs['average']:.2f}")
            print(f"   최종: {fs['final']:.2f}")
        
        convergence = metrics['convergence']
        print(f"🎯 수렴 상태: {convergence['message']}")
        
        if self.best_solutions:
            best = self.best_solutions[0]
            print(f"🏆 최고 솔루션:")
            print(f"   적합도: {best['fitness']:.2f}")
            print(f"   배치 코드: {best.get('code', 'N/A')}")


class MultiObjectiveOptimizationEngine(OptimizationEngine):
    """다목적 최적화 엔진 기본 클래스"""
    
    def __init__(self, layout_generator, fitness_calculator, constraint_handler, objectives: List[str]):
        """
        초기화
        
        Args:
            layout_generator: 배치 생성기
            fitness_calculator: 적합도 계산기
            constraint_handler: 제약 조건 처리기
            objectives: 최적화 목표 리스트
        """
        super().__init__(layout_generator, fitness_calculator, constraint_handler)
        self.objectives = objectives
        self.pareto_front = []
    
    def evaluate_multi_objective(self, layout: List[Dict[str, Any]]) -> Dict[str, float]:
        """다목적 평가"""
        
        if not self.constraint_handler.is_valid(layout):
            return {obj: float('-inf') for obj in self.objectives}
        
        breakdown = self.fitness_calculator.get_fitness_breakdown(layout)
        
        # 목표별 점수 추출
        objective_scores = {}
        for objective in self.objectives:
            if objective == 'adjacency':
                objective_scores[objective] = breakdown['bonuses']['adjacency']
            elif objective == 'compactness':
                objective_scores[objective] = breakdown['bonuses']['compactness'] 
            elif objective == 'utilization':
                objective_scores[objective] = breakdown['bonuses']['utilization']
            elif objective == 'accessibility':
                objective_scores[objective] = breakdown['bonuses']['accessibility']
            elif objective == 'sequence':
                objective_scores[objective] = breakdown['bonuses']['sequence']
            else:
                objective_scores[objective] = 0.0
        
        return objective_scores
    
    def is_pareto_dominant(self, scores1: Dict[str, float], scores2: Dict[str, float]) -> bool:
        """파레토 우세 관계 확인"""
        
        better_in_any = False
        worse_in_any = False
        
        for objective in self.objectives:
            if scores1[objective] > scores2[objective]:
                better_in_any = True
            elif scores1[objective] < scores2[objective]:
                worse_in_any = True
        
        return better_in_any and not worse_in_any
    
    def update_pareto_front(self, solution: Dict[str, Any]):
        """파레토 프론트 업데이트"""
        
        new_scores = solution['objective_scores']
        
        # 기존 해들 중 새 해에 의해 지배당하는 해들 제거
        self.pareto_front = [
            sol for sol in self.pareto_front 
            if not self.is_pareto_dominant(new_scores, sol['objective_scores'])
        ]
        
        # 새 해가 기존 해들에 의해 지배당하지 않으면 추가
        is_dominated = any(
            self.is_pareto_dominant(sol['objective_scores'], new_scores)
            for sol in self.pareto_front
        )
        
        if not is_dominated:
            self.pareto_front.append(solution)


if __name__ == "__main__":
    # 기본 클래스 테스트는 추상 클래스이므로 구현하지 않음
    print("OptimizationEngine은 추상 기본 클래스입니다.")
    print("하위 클래스 (ExhaustiveSearchOptimizer 등)에서 테스트하세요.")