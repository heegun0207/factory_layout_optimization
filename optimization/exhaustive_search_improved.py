"""
개선된 전수 탐색 최적화 엔진
다중 시드 포인트, 조기 가지치기, 적응형 샘플링이 적용된 고성능 버전
"""

import time
from typing import Dict, List, Any, Optional
from optimization.base_engine import OptimizationEngine


class ImprovedExhaustiveSearchOptimizer(OptimizationEngine):
    """성능 개선된 전수 탐색 기반 최적화 엔진"""
    
    def __init__(self, layout_generator, fitness_calculator, constraint_handler):
        """
        초기화
        
        Args:
            layout_generator: 개선된 배치 생성기 (ImprovedSequenceLayoutGenerator)
            fitness_calculator: 적합도 계산기
            constraint_handler: 제약 조건 처리기
        """
        super().__init__(layout_generator, fitness_calculator, constraint_handler)
        self.name = "개선된 전수 탐색 (Improved Exhaustive Search)"
        
        # 성능 통계
        self.performance_stats = {
            'total_combinations_generated': 0,
            'combinations_evaluated': 0,
            'valid_solutions_found': 0,
            'boundary_violations': 0,
            'constraint_violations': 0,
            'seed_strategies_used': 0,
            'optimization_phases': []
        }
        
        # 최적화 설정
        self.early_termination_threshold = 10  # 충분한 고품질 솔루션 확보 시 조기 종료
        self.quality_threshold = 800           # 고품질 솔루션 기준 점수
        self.progress_update_interval = 50     # 진행률 업데이트 간격
        
        print(f"🚀 {self.name} 초기화 완료")
    
    def optimize(self, 
                main_processes: List[Dict[str, Any]], 
                sub_processes: List[Dict[str, Any]], 
                visualizer=None,
                max_solutions: int = 8,
                max_combinations: int = None,
                enable_early_termination: bool = True,
                **kwargs) -> List[Dict[str, Any]]:
        """
        개선된 전수 탐색 최적화 실행
        
        Args:
            main_processes: 주공정 목록 (순서대로 정렬된 상태)
            sub_processes: 부공정 목록
            visualizer: 실시간 시각화기
            max_solutions: 반환할 최대 솔루션 수
            max_combinations: 처리할 최대 조합 수 (None이면 적응형)
            enable_early_termination: 조기 종료 활성화 여부
            **kwargs: 추가 파라미터
        
        Returns:
            최적화된 솔루션 목록 (적합도 순으로 정렬)
        """
        print(f"🔍 {self.name} 최적화 시작")
        print(f"   📊 설정: 주공정 {len(main_processes)}개, 부공정 {len(sub_processes)}개")
        print(f"   🎯 목표: 상위 {max_solutions}개 솔루션")
        print(f"   ⚡ 조기 종료: {'활성화' if enable_early_termination else '비활성화'}")
        
        start_time = time.time()
        self._reset_performance_stats()
        
        # Phase 1: 주공정 배치 조합 생성 (개선된 알고리즘 적용)
        phase_start = time.time()
        print(f"\n1️⃣ 주공정 배치 조합 생성 중...")
        
        main_layout_combinations = self.layout_generator.generate_main_layout_combinations(main_processes)
        
        if not main_layout_combinations:
            print("❌ 유효한 주공정 배치 조합을 찾지 못했습니다.")
            return []
        
        phase_time = time.time() - phase_start
        self.performance_stats['total_combinations_generated'] = len(main_layout_combinations)
        self.performance_stats['optimization_phases'].append({
            'phase': 'combination_generation',
            'duration': phase_time,
            'combinations': len(main_layout_combinations)
        })
        
        print(f"✅ 조합 생성 완료: {len(main_layout_combinations):,}개 ({phase_time:.2f}초)")
        
        # 조합 수 제한 적용 (레거시 호환)
        if max_combinations and len(main_layout_combinations) > max_combinations:
            print(f"⚡ 조합 수 제한: {len(main_layout_combinations):,} → {max_combinations:,}개")
            main_layout_combinations = main_layout_combinations[:max_combinations]
        
        # Phase 2: 부공정 배치 및 적합도 평가
        phase_start = time.time()
        print(f"\n2️⃣ 부공정 배치 및 적합도 평가 중...")
        
        solutions = self._evaluate_combinations(
            main_layout_combinations, 
            sub_processes,
            visualizer,
            enable_early_termination,
            max_solutions
        )
        
        phase_time = time.time() - phase_start
        self.performance_stats['optimization_phases'].append({
            'phase': 'evaluation',
            'duration': phase_time,
            'solutions_found': len(solutions)
        })
        
        # Phase 3: 결과 정리 및 통계
        end_time = time.time()
        total_time = end_time - start_time
        
        final_solutions = self._finalize_results(solutions, max_solutions)
        
        self._print_optimization_summary(total_time, final_solutions)
        
        return final_solutions
    
    def _evaluate_combinations(self, 
                              main_combinations: List[List[Dict[str, Any]]], 
                              sub_processes: List[Dict[str, Any]],
                              visualizer,
                              enable_early_termination: bool,
                              max_solutions: int) -> List[Dict[str, Any]]:
        """조합들을 평가하여 솔루션 생성"""
        
        solutions = []
        high_quality_solutions = []
        last_update = 0
        
        total_combinations = len(main_combinations)
        
        for i, main_layout in enumerate(main_combinations):
            self.performance_stats['combinations_evaluated'] += 1
            
            # 부공정 배치
            complete_layout = self.layout_generator.place_sub_processes_optimally(
                main_layout, 
                sub_processes,
                self.fitness_calculator.adjacency_weights
            )
            
            # 적합도 평가 (페널티 포함)
            fitness = self._evaluate_solution_with_penalties(complete_layout)
            
            # 제약 조건 검사 및 분류
            is_constraint_valid = self.constraint_handler.is_valid(complete_layout)
            has_boundary_violations = self._has_boundary_violations(complete_layout)
            
            # 통계 업데이트
            if is_constraint_valid:
                self.performance_stats['valid_solutions_found'] += 1
            else:
                self.performance_stats['constraint_violations'] += 1
                if has_boundary_violations:
                    self.performance_stats['boundary_violations'] += 1
            
            # 배치 코드 생성
            layout_code = self.layout_generator.generate_layout_code(complete_layout)
            
            # 솔루션 생성
            solution = {
                'layout': complete_layout,
                'fitness': fitness,
                'code': layout_code,
                'method': 'improved_exhaustive_search',
                'generation': i + 1,
                'evaluation_time': time.time(),
                'constraint_valid': is_constraint_valid,
                'boundary_violations': has_boundary_violations,
                'penalty_score': self._calculate_total_penalty(complete_layout)
            }
            
            # 솔루션 수집
            solutions.append(solution)
            
            # 고품질 솔루션 별도 추적
            if is_constraint_valid and fitness > self.quality_threshold:
                high_quality_solutions.append(solution)
            
            # 베스트 솔루션 업데이트
            self.update_best_solutions(solution, max_solutions * 3)
            self.fitness_history.append(fitness)
            
            # 실시간 시각화 업데이트
            if visualizer and i - last_update >= self.progress_update_interval:
                visualizer.update_progress(
                    current=i + 1,
                    total=total_combinations,
                    best_fitness=max(self.fitness_history) if self.fitness_history else 0,
                    current_layout=complete_layout
                )
                last_update = i
            
            # 진행률 출력 (5% 간격)
            if (i + 1) % max(1, total_combinations // 20) == 0:
                progress = ((i + 1) / total_combinations) * 100
                elapsed = time.time() - self.start_time if hasattr(self, 'start_time') else 0
                print(f"   📊 진행률: {progress:.1f}% ({i + 1:,}/{total_combinations:,}) "
                      f"- 유효: {self.performance_stats['valid_solutions_found']:,}개 "
                      f"- 고품질: {len(high_quality_solutions):,}개 - {elapsed:.1f}초")
            
            # 조기 종료 조건 확인
            if enable_early_termination and self._should_early_terminate(
                high_quality_solutions, i + 1, total_combinations, max_solutions
            ):
                print(f"⚡ 조기 종료: 충분한 고품질 솔루션 ({len(high_quality_solutions)}개) 확보")
                break
        
        return solutions
    
    def _should_early_terminate(self, 
                               high_quality_solutions: List[Dict[str, Any]], 
                               current_iteration: int,
                               total_combinations: int,
                               target_solutions: int) -> bool:
        """조기 종료 조건 확인"""
        
        # 최소 진행률 보장 (전체의 10% 이상은 탐색)
        min_progress = 0.1
        if current_iteration < total_combinations * min_progress:
            return False
        
        # 충분한 고품질 솔루션 확보
        if len(high_quality_solutions) >= target_solutions * 2:
            return True
        
        # 진행률이 50% 이상이고 목표 수의 고품질 솔루션 확보
        if (current_iteration >= total_combinations * 0.5 and 
            len(high_quality_solutions) >= target_solutions):
            return True
        
        # 최근 일정 구간에서 개선이 없는 경우 (수렴 판정)
        if (len(self.fitness_history) > 100 and 
            current_iteration >= total_combinations * 0.3):
            
            recent_scores = self.fitness_history[-50:]  # 최근 50개
            if recent_scores:
                recent_best = max(recent_scores)
                overall_best = max(self.fitness_history)
                
                # 최근 구간의 최고 점수가 전체 최고 점수의 95% 미만이면 수렴
                if recent_best < overall_best * 0.95 and len(high_quality_solutions) > 0:
                    return True
        
        return False
    
    def _evaluate_solution_with_penalties(self, layout: List[Dict[str, Any]]) -> float:
        """페널티를 포함한 솔루션 평가"""
        
        # 기본 적합도 계산
        base_fitness = self.fitness_calculator.calculate_fitness(layout)
        
        # 제약 조건 위반 페널티 계산
        penalty = self._calculate_total_penalty(layout)
        
        # 최종 적합도 = 기본 적합도 - 페널티
        final_fitness = base_fitness - penalty
        
        return final_fitness
    
    def _calculate_total_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """총 페널티 계산"""
        
        penalty = 0.0
        
        # 1. 경계 위반 페널티
        penalty += self._calculate_boundary_penalty(layout)
        
        # 2. 겹침 페널티
        penalty += self._calculate_overlap_penalty(layout)
        
        # 3. 고정구역 침범 페널티
        penalty += self._calculate_fixed_zone_penalty(layout)
        
        return penalty
    
    def _calculate_boundary_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """경계 위반 페널티 계산"""
        penalty = 0.0
        
        for rect in layout:
            # 경계 위반 거리 계산
            x_violation = max(0, -rect['x']) + max(0, rect['x'] + rect['width'] - self.layout_generator.site_width)
            y_violation = max(0, -rect['y']) + max(0, rect['y'] + rect['height'] - self.layout_generator.site_height)
            
            # 위반 거리에 비례한 페널티
            penalty += (x_violation + y_violation) * 10
        
        return penalty
    
    def _calculate_overlap_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """겹침 페널티 계산"""
        penalty = 0.0
        
        for i in range(len(layout)):
            for j in range(i + 1, len(layout)):
                rect1, rect2 = layout[i], layout[j]
                
                if self.layout_generator.geometry.rectangles_overlap(rect1, rect2):
                    overlap_area = self.layout_generator.geometry.calculate_overlap_area(rect1, rect2)
                    penalty += overlap_area * 100  # 겹침 면적 × 100
        
        return penalty
    
    def _calculate_fixed_zone_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """고정구역 침범 페널티 계산"""
        penalty = 0.0
        
        for rect in layout:
            for fixed_zone in self.layout_generator.fixed_zones:
                if self.layout_generator.geometry.rectangles_overlap(rect, fixed_zone):
                    overlap_area = self.layout_generator.geometry.calculate_overlap_area(rect, fixed_zone)
                    penalty += overlap_area * 50  # 침범 면적 × 50
        
        return penalty
    
    def _has_boundary_violations(self, layout: List[Dict[str, Any]]) -> bool:
        """경계 위반 여부 확인"""
        for rect in layout:
            if (rect['x'] < 0 or rect['y'] < 0 or 
                rect['x'] + rect['width'] > self.layout_generator.site_width or 
                rect['y'] + rect['height'] > self.layout_generator.site_height):
                return True
        return False
    
    def _finalize_results(self, solutions: List[Dict[str, Any]], max_solutions: int) -> List[Dict[str, Any]]:
        """결과 정리 및 최종 선택"""
        
        if not solutions:
            return []
        
        # 적합도 순으로 정렬
        sorted_solutions = sorted(solutions, key=lambda x: x['fitness'], reverse=True)
        
        # 상위 솔루션 선택 (제약 조건 준수 솔루션 우선)
        final_solutions = []
        constraint_valid_solutions = []
        boundary_violation_solutions = []
        
        # 분류
        for solution in sorted_solutions:
            if solution['constraint_valid']:
                constraint_valid_solutions.append(solution)
            elif solution['boundary_violations']:
                boundary_violation_solutions.append(solution)
        
        # 우선순위: 제약준수 > 경계위반 > 기타
        final_solutions.extend(constraint_valid_solutions[:max_solutions])
        
        if len(final_solutions) < max_solutions:
            remaining = max_solutions - len(final_solutions)
            final_solutions.extend(boundary_violation_solutions[:remaining])
        
        # 여전히 부족하면 나머지로 채우기
        if len(final_solutions) < max_solutions:
            remaining = max_solutions - len(final_solutions)
            other_solutions = [s for s in sorted_solutions 
                             if s not in constraint_valid_solutions and 
                                s not in boundary_violation_solutions]
            final_solutions.extend(other_solutions[:remaining])
        
        return final_solutions[:max_solutions]
    
    def _reset_performance_stats(self):
        """성능 통계 초기화"""
        self.start_time = time.time()
        self.performance_stats = {
            'total_combinations_generated': 0,
            'combinations_evaluated': 0,
            'valid_solutions_found': 0,
            'boundary_violations': 0,
            'constraint_violations': 0,
            'seed_strategies_used': 0,
            'optimization_phases': []
        }
    
    def _print_optimization_summary(self, total_time: float, solutions: List[Dict[str, Any]]):
        """최적화 결과 요약 출력"""
        
        print(f"\n✅ {self.name} 최적화 완료!")
        print(f"=" * 60)
        
        # 시간 정보
        print(f"⏱️  총 소요시간: {total_time:.2f}초")
        
        phase_times = {phase['phase']: phase['duration'] for phase in self.performance_stats['optimization_phases']}
        if 'combination_generation' in phase_times:
            print(f"   └─ 조합 생성: {phase_times['combination_generation']:.2f}초")
        if 'evaluation' in phase_times:
            print(f"   └─ 평가 단계: {phase_times['evaluation']:.2f}초")
        
        # 조합 및 평가 통계
        print(f"📊 처리 통계:")
        print(f"   🔄 생성된 조합: {self.performance_stats['total_combinations_generated']:,}개")
        print(f"   🔍 평가된 조합: {self.performance_stats['combinations_evaluated']:,}개")
        
        eval_rate = self.performance_stats['combinations_evaluated'] / total_time if total_time > 0 else 0
        print(f"   ⚡ 평가 속도: {eval_rate:.1f}개/초")
        
        # 솔루션 품질 통계
        print(f"🎯 솔루션 품질:")
        print(f"   ✅ 제약준수: {self.performance_stats['valid_solutions_found']:,}개 "
              f"({self.performance_stats['valid_solutions_found']/max(1,self.performance_stats['combinations_evaluated'])*100:.1f}%)")
        print(f"   ⚠️  경계초과: {self.performance_stats['boundary_violations']:,}개")
        print(f"   ❌ 제약위반: {self.performance_stats['constraint_violations']:,}개")
        
        # 최종 결과
        print(f"🏆 최종 결과: {len(solutions)}개 솔루션")
        
        if solutions:
            best_solution = solutions[0]
            constraint_valid_count = sum(1 for s in solutions if s['constraint_valid'])
            
            print(f"   🥇 최고 적합도: {best_solution['fitness']:.2f}")
            print(f"      └─ 제약준수: {'✅' if best_solution['constraint_valid'] else '❌'}")
            print(f"      └─ 경계준수: {'✅' if not best_solution['boundary_violations'] else '❌'}")
            print(f"      └─ 배치코드: {best_solution['code']}")
            
            print(f"   📈 품질 분포:")
            print(f"      └─ 제약준수 솔루션: {constraint_valid_count}/{len(solutions)}개")
            
            # 적합도 범위
            fitness_scores = [s['fitness'] for s in solutions]
            print(f"      └─ 적합도 범위: {min(fitness_scores):.1f} ~ {max(fitness_scores):.1f}")
        
        # 성능 개선 효과 출력
        if hasattr(self.layout_generator, 'stats'):
            print(f"🚀 성능 최적화 효과:")
            gen_stats = self.layout_generator.stats
            
            if gen_stats.get('pruned_rotations', 0) > 0 or gen_stats.get('pruned_directions', 0) > 0:
                print(f"   ✂️  조기 가지치기: 회전 {gen_stats.get('pruned_rotations', 0):,}개, "
                      f"방향 {gen_stats.get('pruned_directions', 0):,}개 제거")
            
            if gen_stats.get('sampled_combinations', 0) > 0:
                print(f"   🎲 적응형 샘플링: {gen_stats.get('sampled_combinations', 0):,}개 조합 처리")
            
            if gen_stats.get('seed_positions_used', 0) > 0:
                print(f"   📍 다중 시드: {gen_stats.get('seed_positions_used', 0)}개 전략적 위치 활용")
        
        print(f"=" * 60)
    
    def get_detailed_performance_report(self) -> Dict[str, Any]:
        """상세 성능 리포트 생성"""
        
        total_time = self.get_optimization_time()
        
        report = {
            'algorithm': self.name,
            'optimization_time': total_time,
            'performance_stats': self.performance_stats.copy(),
            'solution_stats': {
                'total_found': len(self.best_solutions),
                'fitness_range': {
                    'min': min(s['fitness'] for s in self.best_solutions) if self.best_solutions else 0,
                    'max': max(s['fitness'] for s in self.best_solutions) if self.best_solutions else 0,
                    'avg': sum(s['fitness'] for s in self.best_solutions) / len(self.best_solutions) if self.best_solutions else 0
                },
                'constraint_compliance_rate': (
                    sum(1 for s in self.best_solutions if s.get('constraint_valid', False)) / 
                    len(self.best_solutions) if self.best_solutions else 0
                )
            },
            'efficiency_metrics': {
                'combinations_per_second': (
                    self.performance_stats['combinations_evaluated'] / total_time if total_time > 0 else 0
                ),
                'success_rate': (
                    self.performance_stats['valid_solutions_found'] / 
                    max(1, self.performance_stats['combinations_evaluated'])
                ),
                'phase_breakdown': {
                    phase['phase']: {
                        'duration': phase['duration'],
                        'percentage': phase['duration'] / total_time * 100 if total_time > 0 else 0
                    }
                    for phase in self.performance_stats['optimization_phases']
                }
            }
        }
        
        # 레거시 최적화 기법별 효과 분석
        if hasattr(self.layout_generator, 'stats'):
            gen_stats = self.layout_generator.stats
            
            # 가지치기 효과
            total_pruned = gen_stats.get('pruned_rotations', 0) + gen_stats.get('pruned_directions', 0)
            if total_pruned > 0:
                original_combinations = (
                    self.performance_stats['combinations_evaluated'] + 
                    total_pruned * gen_stats.get('seed_positions_used', 1)
                )
                pruning_efficiency = total_pruned / original_combinations if original_combinations > 0 else 0
                report['optimization_techniques'] = {
                    'early_pruning': {
                        'enabled': True,
                        'combinations_pruned': total_pruned,
                        'efficiency_gain': pruning_efficiency
                    }
                }
            
            # 샘플링 효과
            if gen_stats.get('sampled_combinations', 0) > 0:
                report['optimization_techniques'] = report.get('optimization_techniques', {})
                report['optimization_techniques']['adaptive_sampling'] = {
                    'enabled': True,
                    'sample_size': gen_stats.get('sampled_combinations', 0),
                    'seed_positions': gen_stats.get('seed_positions_used', 0)
                }
        
        return report
    
    def compare_with_baseline(self, baseline_time: float, baseline_solutions: int) -> Dict[str, Any]:
        """기존 방식과의 성능 비교"""
        
        current_time = self.get_optimization_time()
        current_solutions = len(self.best_solutions)
        
        comparison = {
            'time_improvement': {
                'baseline_time': baseline_time,
                'current_time': current_time,
                'speedup_ratio': baseline_time / current_time if current_time > 0 else float('inf'),
                'time_saved': baseline_time - current_time
            },
            'solution_quality': {
                'baseline_solutions': baseline_solutions,
                'current_solutions': current_solutions,
                'improvement_ratio': current_solutions / baseline_solutions if baseline_solutions > 0 else float('inf')
            },
            'overall_efficiency': {
                'baseline_efficiency': baseline_solutions / baseline_time if baseline_time > 0 else 0,
                'current_efficiency': current_solutions / current_time if current_time > 0 else 0
            }
        }
        
        # 개선 효과 평가
        speedup = comparison['time_improvement']['speedup_ratio']
        if speedup > 2:
            comparison['performance_grade'] = 'Excellent'
        elif speedup > 1.5:
            comparison['performance_grade'] = 'Good'
        elif speedup > 1.1:
            comparison['performance_grade'] = 'Moderate'
        else:
            comparison['performance_grade'] = 'Minimal'
        
        return comparison
    
    def export_optimization_log(self, filepath: str = None):
        """최적화 과정 로그 내보내기"""
        
        import json
        from datetime import datetime
        
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"optimization_log_{timestamp}.json"
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'algorithm': self.name,
            'performance_report': self.get_detailed_performance_report(),
            'optimization_history': self.optimization_history,
            'fitness_evolution': self.fitness_history,
            'best_solutions': [
                {
                    'fitness': sol['fitness'],
                    'code': sol.get('code', ''),
                    'constraint_valid': sol.get('constraint_valid', False),
                    'generation': sol.get('generation', 0)
                }
                for sol in self.best_solutions[:10]  # 상위 10개만
            ]
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📋 최적화 로그 저장 완료: {filepath}")
            
        except Exception as e:
            print(f"❌ 로그 저장 실패: {str(e)}")


# 기존 코드와의 호환성을 위한 별칭
ImprovedExhaustiveSearchEngine = ImprovedExhaustiveSearchOptimizer
