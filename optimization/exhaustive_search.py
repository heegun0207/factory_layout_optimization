"""
전수 탐색 최적화 엔진 (제약 조건 완화 버전)
Factory Mass Layout Algorithm을 기반으로 모든 가능한 주공정 배치 조합을 탐색합니다.
경계 초과 솔루션도 평가하되 적합도에 페널티를 부여합니다.
"""

import time
from typing import Dict, List, Any, Optional
from optimization.base_engine import OptimizationEngine


class ExhaustiveSearchOptimizer(OptimizationEngine):
    """전수 탐색 기반 최적화 엔진 (제약 조건 완화 버전)"""
    
    def __init__(self, layout_generator, fitness_calculator, constraint_handler):
        """
        초기화
        
        Args:
            layout_generator: 배치 생성기
            fitness_calculator: 적합도 계산기
            constraint_handler: 제약 조건 처리기
        """
        super().__init__(layout_generator, fitness_calculator, constraint_handler)
        self.name = "전수 탐색 (Exhaustive Search)"
        self.evaluated_combinations = 0
        self.valid_combinations = 0
        self.boundary_violations = 0
        self.constraint_violations = 0
        
    def optimize(self, 
                main_processes: List[Dict[str, Any]], 
                sub_processes: List[Dict[str, Any]], 
                visualizer=None,
                max_solutions: int = 8,
                max_combinations: int = None,  # 🚀 처리할 최대 조합 수 제한
                **kwargs) -> List[Dict[str, Any]]:
        """
        전수 탐색 최적화 실행 (제약 조건 완화)
        
        Args:
            main_processes: 주공정 목록 (순서대로 정렬된 상태)
            sub_processes: 부공정 목록
            visualizer: 실시간 시각화기 (선택사항)
            max_solutions: 반환할 최대 솔루션 수
            **kwargs: 추가 파라미터
        
        Returns:
            최적화된 솔루션 목록 (적합도 순으로 정렬)
        """
        print(f"🔍 {self.name} 최적화 시작 (제약 조건 완화)")
        print(f"   주공정: {len(main_processes)}개")
        print(f"   부공정: {len(sub_processes)}개")
        
        start_time = time.time()
        self.best_solutions = []
        self.fitness_history = []
        self.evaluated_combinations = 0
        self.valid_combinations = 0
        self.boundary_violations = 0
        self.constraint_violations = 0
        
        # 1단계: 주공정 배치 조합 생성
        print("\n1️⃣ 주공정 배치 조합 생성 중...")
        main_layout_combinations = self.layout_generator.generate_main_layout_combinations(main_processes)
        
        if not main_layout_combinations:
            print("❌ 유효한 주공정 배치 조합을 찾지 못했습니다.")
            return []
        
        # 🚀 조합 수 제한 (테스트 모드)
        if max_combinations and len(main_layout_combinations) > max_combinations:
            print(f"⚡ 테스트 모드: {len(main_layout_combinations)}개 중 상위 {max_combinations}개만 처리")
            main_layout_combinations = main_layout_combinations[:max_combinations]
        
        total_combinations = len(main_layout_combinations)
        print(f"✅ 주공정 배치 조합: {total_combinations}개")
        
        # 2단계: 각 주공정 배치에 부공정 추가 및 평가
        print(f"\n2️⃣ 부공정 배치 및 적합도 평가 중... (모든 솔루션 평가)")
        
        update_interval = max(1, total_combinations // 20)  # 5% 간격으로 업데이트
        
        for i, main_layout in enumerate(main_layout_combinations):
            self.evaluated_combinations += 1
            
            # 🚀 진행률 표시 개선
            if i % max(1, total_combinations // 20) == 0 or i < 10:
                progress = ((i + 1) / total_combinations) * 100
                print(f"   📊 부공정 배치 진행률: {progress:.1f}% ({i + 1}/{total_combinations})")
            
            # 부공정 추가
            complete_layout = self.layout_generator.place_sub_processes_optimally(
                main_layout, 
                sub_processes,
                self.fitness_calculator.adjacency_weights
            )
            
            # ⭐ 핵심 변경: 모든 솔루션을 평가 (제약 조건 위반과 관계없이)
            fitness = self._evaluate_solution_with_penalties(complete_layout)
            
            # 솔루션 분류
            is_constraint_valid = self.constraint_handler.is_valid(complete_layout)
            has_boundary_violations = self._has_boundary_violations(complete_layout)
            
            if is_constraint_valid:
                self.valid_combinations += 1
            else:
                self.constraint_violations += 1
                if has_boundary_violations:
                    self.boundary_violations += 1
            
            # 배치 코드 생성
            layout_code = self.layout_generator.generate_layout_code(complete_layout)
            
            # 솔루션 생성 (제약 위반 정보 포함)
            solution = {
                'layout': complete_layout,
                'fitness': fitness,
                'code': layout_code,
                'method': 'exhaustive_search',
                'generation': i + 1,
                'evaluation_time': time.time() - start_time,
                'constraint_valid': is_constraint_valid,
                'boundary_violations': has_boundary_violations,
                'penalty_score': fitness - self.fitness_calculator.calculate_fitness(complete_layout) if is_constraint_valid else 0
            }
            
            # 베스트 솔루션 업데이트 (모든 솔루션 포함)
            self.update_best_solutions(solution, max_solutions * 3)  # 더 여유있게 수집
            self.fitness_history.append(fitness)
            
            # 실시간 시각화 업데이트
            if visualizer and i % update_interval == 0:
                visualizer.update_progress(
                    current=i + 1,
                    total=total_combinations,
                    best_fitness=max(self.fitness_history) if self.fitness_history else 0,
                    current_layout=complete_layout
                )
            
            # 진행률 출력 (5% 간격으로 더 자주)
            if (i + 1) % max(1, total_combinations // 20) == 0:
                progress = ((i + 1) / total_combinations) * 100
                elapsed = time.time() - start_time
                print(f"   진행률: {progress:.1f}% ({i + 1}/{total_combinations}) "
                      f"- 제약준수: {self.valid_combinations}개, 경계초과: {self.boundary_violations}개 - {elapsed:.1f}초")
                
                # 🚀 조기 종료 조건 (충분한 고품질 솔루션 확보 시)
                if len(self.best_solutions) >= max_solutions * 3 and self.valid_combinations >= max_solutions:
                    high_quality_solutions = [s for s in self.best_solutions if s.get('constraint_valid', False)]
                    if len(high_quality_solutions) >= max_solutions:
                        print(f"⚡ 조기 종료: 충분한 고품질 솔루션 ({len(high_quality_solutions)}개) 확보")
                        break
        
        end_time = time.time()
        optimization_time = end_time - start_time
        
        # 결과 정리
        final_solutions = sorted(self.best_solutions, key=lambda x: x['fitness'], reverse=True)[:max_solutions]
        
        print(f"\n✅ {self.name} 최적화 완료!")
        print(f"   ⏱️  소요시간: {optimization_time:.2f}초")
        print(f"   📊 평가된 조합: {self.evaluated_combinations:,}개")
        print(f"   ✅ 제약준수 솔루션: {self.valid_combinations}개 ({self.valid_combinations/self.evaluated_combinations*100:.1f}%)")
        print(f"   ⚠️  경계초과 솔루션: {self.boundary_violations}개 ({self.boundary_violations/self.evaluated_combinations*100:.1f}%)")
        print(f"   🎯 최종 솔루션: {len(final_solutions)}개")
        
        if final_solutions:
            best_solution = final_solutions[0]
            print(f"   🏆 최고 적합도: {best_solution['fitness']:.2f}")
            print(f"      제약준수: {'✅' if best_solution['constraint_valid'] else '❌'}")
            print(f"      경계초과: {'❌' if best_solution['boundary_violations'] else '✅'}")
        
        return final_solutions
    
    def _evaluate_solution_with_penalties(self, layout: List[Dict[str, Any]]) -> float:
        """
        페널티를 포함한 솔루션 평가
        
        Args:
            layout: 평가할 배치
        
        Returns:
            페널티가 포함된 적합도 점수
        """
        # 기본 적합도 계산
        base_fitness = self.fitness_calculator.calculate_fitness(layout)
        
        # 제약 조건 위반 페널티 계산
        penalty = 0.0
        
        # 1. 경계 위반 페널티
        boundary_penalty = self._calculate_boundary_penalty(layout)
        penalty += boundary_penalty
        
        # 2. 겹침 페널티
        overlap_penalty = self._calculate_overlap_penalty(layout)
        penalty += overlap_penalty
        
        # 3. 고정구역 침범 페널티
        fixed_zone_penalty = self._calculate_fixed_zone_penalty(layout)
        penalty += fixed_zone_penalty
        
        # 최종 적합도 = 기본 적합도 - 페널티
        final_fitness = base_fitness - penalty
        
        return final_fitness
    
    def _has_boundary_violations(self, layout: List[Dict[str, Any]]) -> bool:
        """경계 위반 여부 확인"""
        for rect in layout:
            if (rect['x'] < 0 or rect['y'] < 0 or 
                rect['x'] + rect['width'] > self.layout_generator.site_width or 
                rect['y'] + rect['height'] > self.layout_generator.site_height):
                return True
        return False
    
    def _calculate_boundary_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """경계 위반 페널티 계산"""
        penalty = 0.0
        
        for rect in layout:
            # 왼쪽/위쪽 경계 위반
            if rect['x'] < 0:
                penalty += abs(rect['x']) * 10  # 경계 밖 거리 × 10
            if rect['y'] < 0:
                penalty += abs(rect['y']) * 10
            
            # 오른쪽/아래쪽 경계 위반
            right_excess = rect['x'] + rect['width'] - self.layout_generator.site_width
            if right_excess > 0:
                penalty += right_excess * 10
            
            bottom_excess = rect['y'] + rect['height'] - self.layout_generator.site_height
            if bottom_excess > 0:
                penalty += bottom_excess * 10
        
        return penalty
    
    def _calculate_overlap_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """겹침 페널티 계산"""
        penalty = 0.0
        
        for i in range(len(layout)):
            for j in range(i + 1, len(layout)):
                rect1, rect2 = layout[i], layout[j]
                
                # 겹치는 영역 계산
                overlap_area = self._calculate_overlap_area(rect1, rect2)
                if overlap_area > 0:
                    penalty += overlap_area * 100  # 겹침 면적 × 100
        
        return penalty
    
    def _calculate_overlap_area(self, rect1: Dict[str, Any], rect2: Dict[str, Any]) -> float:
        """두 사각형의 겹치는 영역 계산"""
        x_overlap = max(0, min(rect1['x'] + rect1['width'], rect2['x'] + rect2['width']) - 
                          max(rect1['x'], rect2['x']))
        y_overlap = max(0, min(rect1['y'] + rect1['height'], rect2['y'] + rect2['height']) - 
                          max(rect1['y'], rect2['y']))
        return x_overlap * y_overlap
    
    def _calculate_fixed_zone_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """고정구역 침범 페널티 계산"""
        penalty = 0.0
        
        for rect in layout:
            for zone in self.layout_generator.fixed_zones:
                overlap_area = self._calculate_overlap_area(rect, zone)
                if overlap_area > 0:
                    penalty += overlap_area * 50  # 침범 면적 × 50
        
        return penalty
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """최적화 통계 정보 반환 (확장된 버전)"""
        base_stats = super().get_performance_metrics()
        
        # 제약 조건 관련 통계 추가
        if self.evaluated_combinations > 0:
            base_stats['constraint_statistics'] = {
                'total_evaluated': self.evaluated_combinations,
                'valid_solutions': self.valid_combinations,
                'boundary_violations': self.boundary_violations,
                'constraint_violations': self.constraint_violations,
                'valid_rate': self.valid_combinations / self.evaluated_combinations,
                'boundary_violation_rate': self.boundary_violations / self.evaluated_combinations
            }
        
        return base_stats


# 이전 버전과의 호환성을 위한 별칭
ExhaustiveSearchEngine = ExhaustiveSearchOptimizer
