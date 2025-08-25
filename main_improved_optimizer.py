#!/usr/bin/env python3
"""
개선된 공정 순서 기반 배치 최적화 메인 실행 스크립트
다중 시드 포인트, 조기 가지치기, 적응형 샘플링이 적용된 고성능 버전
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional  # 이 줄 추가

# 기존 모듈들
try:
    from core.config_loader import ConfigLoader
    from core.process_classifier import ProcessClassifier
    from core.fitness_calculator import FitnessCalculator
    from core.constraint_handler import ConstraintHandler
    from utils.geometry_utils import GeometryUtils
except ImportError as e:
    print(f"❌ 기본 모듈 임포트 오류: {e}")
    print("   프로젝트 구조를 확인하고 모든 필요한 파일이 있는지 확인해주세요.")
    sys.exit(1)

# 개선된 모듈들
try:
    from core.layout_generator_improved import ImprovedSequenceLayoutGenerator
    from optimization.exhaustive_search_improved import ImprovedExhaustiveSearchOptimizer
    print("🚀 개선된 모듈 로드 완료")
except ImportError as e:
    print(f"⚠️ 개선된 모듈 임포트 오류: {e}")
    print("   기존 모듈로 대체합니다.")
    try:
        from core.layout_generator import SequenceLayoutGenerator as ImprovedSequenceLayoutGenerator
        from optimization.exhaustive_search import ExhaustiveSearchOptimizer as ImprovedExhaustiveSearchOptimizer
        print("📦 기존 모듈로 대체 완료")
    except ImportError as fallback_error:
        print(f"❌ 대체 모듈도 로드 실패: {fallback_error}")
        sys.exit(1)

# 시각화 모듈 (선택적)
try:
    from visualization.realtime_visualizer import RealtimeVisualizer
    from visualization.result_visualizer import ResultVisualizer
    VISUALIZATION_AVAILABLE = True
except ImportError:
    print("⚠️ 시각화 모듈이 없습니다. 콘솔 모드로 실행됩니다.")
    VISUALIZATION_AVAILABLE = False
    
    # 대체 시각화 클래스
    class RealtimeVisualizer:
        def __init__(self, *args, **kwargs): 
            pass
        def start_optimization(self): 
            print("📺 콘솔 모드 - 진행률만 표시됩니다.")
        def stop_optimization(self): 
            pass
        def update_progress(self, *args, **kwargs): 
            pass

    class ResultVisualizer:
        def __init__(self, *args, **kwargs): 
            pass
        def show_results(self, solutions):
            if solutions:
                print(f"\n🏆 최적화 결과 ({len(solutions)}개 솔루션)")
                print("=" * 60)
                for i, sol in enumerate(solutions[:8], 1):
                    fitness = sol['fitness']
                    code = sol.get('code', 'N/A')
                    constraint_valid = sol.get('constraint_valid', '알 수 없음')
                    boundary_violations = sol.get('boundary_violations', '알 수 없음')
                    
                    status = "✅" if constraint_valid else "⚠️"
                    boundary_status = "❌" if boundary_violations else "✅"
                    
                    print(f"   #{i:2d}. 적합도: {fitness:7.2f} | 제약준수: {status} | 경계준수: {boundary_status}")
                    print(f"        코드: {code}")
                print("=" * 60)


class ImprovedProcessSequenceOptimizer:
    """성능 개선된 공정 순서 기반 배치 최적화 메인 컨트롤러"""
    
    def __init__(self, config_path: str, performance_mode: str = "balanced"):
        """
        초기화
        
        Args:
            config_path: JSON 설정 파일 경로
            performance_mode: 성능 모드 ("fast", "balanced", "thorough")
        """
        print("🏭 개선된 공정 순서 기반 배치 최적화 시스템 초기화 중...")
        
        self.performance_mode = performance_mode
        self._configure_performance_settings()
        
        # 1. 설정 파일 로드
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load_config()
        
        # 2. 공정 분류 및 검증
        self.process_classifier = ProcessClassifier(self.config)
        self.main_processes, self.sub_processes = self.process_classifier.classify_processes()
        
        # 3. 핵심 모듈 초기화
        self.layout_generator = ImprovedSequenceLayoutGenerator(
            site_width=self.config['site_dimensions']['width'],
            site_height=self.config['site_dimensions']['height'],
            fixed_zones=self.config.get('fixed_zones', [])
        )
       
       
        self.fitness_calculator = FitnessCalculator(
            adjacency_weights=self.config.get('adjacency_weights', {}),
            spaces=self.config['spaces'],
            fixed_zones=self.config.get('fixed_zones', []),
            site_width=self.config['site_dimensions']['width'],
            site_height=self.config['site_dimensions']['height']
        )
        
        self.constraint_handler = ConstraintHandler(
            site_width=self.config['site_dimensions']['width'],
            site_height=self.config['site_dimensions']['height'],
            fixed_zones=self.config.get('fixed_zones', []),
            hazard_factors=self.config.get('hazard_factors', {})
        )
        
        # 4. 개선된 최적화 엔진 초기화
        self.optimizer = ImprovedExhaustiveSearchOptimizer(
            self.layout_generator, 
            self.fitness_calculator, 
            self.constraint_handler
        )

        # 성능 모드별 설정 적용
        self._apply_performance_settings()


        # 5. 시각화 모듈 초기화
        self.realtime_visualizer = RealtimeVisualizer(
            site_width=self.config['site_dimensions']['width'],
            site_height=self.config['site_dimensions']['height']
        )
        
        self.result_visualizer = ResultVisualizer(
            site_width=self.config['site_dimensions']['width'],
            site_height=self.config['site_dimensions']['height']
        )
        
        print("✅ 개선된 시스템 초기화 완료!")
        self._print_system_info()
        self._print_performance_settings()
    
    def _configure_performance_settings(self):
        """성능 모드별 설정 구성"""
        
        performance_configs = {
            "fast": {
                "max_combinations_threshold": 1000,
                "target_sample_size": 200,
                "max_seed_positions": 3,
                "enable_early_termination": True,
                "quality_threshold": 600,
                "description": "빠른 실행 - 기본 품질"
            },
            "balanced": {
                "max_combinations_threshold": 3000,
                "target_sample_size": 800,
                "max_seed_positions": 5,
                "enable_early_termination": True,
                "quality_threshold": 800,
                "description": "균형 모드 - 적당한 속도와 품질"
            },
            "thorough": {
                "max_combinations_threshold": 10000,
                "target_sample_size": 2000,
                "max_seed_positions": 8,
                "enable_early_termination": False,
                "quality_threshold": 900,
                "description": "철저한 탐색 - 최고 품질"
            }
        }
        
        self.perf_config = performance_configs.get(self.performance_mode, performance_configs["balanced"])
        
        if self.performance_mode not in performance_configs:
            print(f"⚠️ 알 수 없는 성능 모드 '{self.performance_mode}', 'balanced' 모드 사용")
            self.performance_mode = "balanced"
    
    def _apply_performance_settings(self):
        """레이아웃 생성기에 성능 설정 적용"""
        
        if hasattr(self.layout_generator, 'max_combinations_threshold'):
            self.layout_generator.max_combinations_threshold = self.perf_config["max_combinations_threshold"]
            self.layout_generator.target_sample_size = self.perf_config["target_sample_size"]
            self.layout_generator.max_seed_positions = self.perf_config["max_seed_positions"]
        
        if hasattr(self.optimizer, 'quality_threshold'):
            self.optimizer.quality_threshold = self.perf_config["quality_threshold"]
    
    def _print_system_info(self):
        """시스템 정보 출력"""
        print("\n📊 시스템 정보:")
        print(f"   📐 부지 크기: {self.config['site_dimensions']['width']}×{self.config['site_dimensions']['height']}m")
        print(f"   🏭 주공정: {len(self.main_processes)}개")
        print(f"   🔧 부공정: {len(self.sub_processes)}개")
        print(f"   🚧 고정구역: {len(self.config.get('fixed_zones', []))}개")
        print(f"   🔗 인접성 규칙: {len(self.config.get('adjacency_weights', {}))}개")
        
        # 주공정 순서 출력
        if self.main_processes:
            print("\n📋 주공정 배치 순서:")
            for i, process in enumerate(self.main_processes, 1):
                sequence = process.get('main_process_sequence', 'N/A')
                print(f"   {i}. {process['id']} (순서: {sequence}) - {process['width']}×{process['height']}m")
    
    def _print_performance_settings(self):
        """성능 설정 정보 출력"""
        print(f"\n🚀 성능 최적화 설정 ({self.performance_mode.upper()} 모드):")
        print(f"   📝 {self.perf_config['description']}")
        print(f"   🎯 조합 임계값: {self.perf_config['max_combinations_threshold']:,}개")
        print(f"   🎲 샘플 크기: {self.perf_config['target_sample_size']:,}개")
        print(f"   📍 시드 포인트: 최대 {self.perf_config['max_seed_positions']}개")
        print(f"   ⚡ 조기 종료: {'활성화' if self.perf_config['enable_early_termination'] else '비활성화'}")
        print(f"   🏆 품질 임계값: {self.perf_config['quality_threshold']}점")
    
    def optimize(self, 
                max_solutions: int = 8,
                enable_visualization: bool = True,
                save_results: bool = True,
                **kwargs) -> List[Dict[str, Any]]:
        """
        개선된 최적화 실행
        
        Args:
            max_solutions: 반환할 최대 솔루션 수
            enable_visualization: 실시간 시각화 활성화
            save_results: 결과 자동 저장 여부
            **kwargs: 추가 최적화 파라미터
        
        Returns:
            최적화된 솔루션 목록
        """
        print(f"\n🚀 {self.performance_mode.upper()} 모드로 최적화 시작...")
        start_time = time.time()
        
        # 실시간 시각화 시작
        if enable_visualization and VISUALIZATION_AVAILABLE:
            self.realtime_visualizer.start_optimization()
        
        try:
            # 최적화 실행
            solutions = self.optimizer.optimize(
                self.main_processes, 
                self.sub_processes,
                visualizer=self.realtime_visualizer if enable_visualization else None,
                max_solutions=max_solutions,
                enable_early_termination=self.perf_config["enable_early_termination"],
                **kwargs
            )
            
            end_time = time.time()
            optimization_time = end_time - start_time
            
            print(f"\n🎉 최적화 성공!")
            print(f"   ⏱️  총 소요시간: {optimization_time:.2f}초")
            print(f"   🏆 발견된 솔루션: {len(solutions)}개")
            
            if solutions:
                best_fitness = solutions[0]['fitness']
                print(f"   🥇 최고 적합도: {best_fitness:.2f}점")
                
                # 결과 시각화
                self.result_visualizer.show_results(solutions)
                
                # 결과 자동 저장
                if save_results:
                    self.save_results(solutions)
                
                # 성능 보고서 생성
                self._generate_performance_report(optimization_time, solutions)
                
                return solutions
            else:
                print("❌ 유효한 솔루션을 찾지 못했습니다.")
                return []
                
        except Exception as e:
            print(f"❌ 최적화 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
        
        finally:
            # 실시간 시각화 종료
            if enable_visualization and VISUALIZATION_AVAILABLE:
                self.realtime_visualizer.stop_optimization()
    
    def benchmark_performance_modes(self, test_duration: int = 60) -> Dict[str, Any]:
        """성능 모드별 벤치마크 실행"""
        
        print(f"\n🏃 성능 모드 벤치마크 실행 (각 {test_duration}초)")
        print("=" * 60)
        
        benchmark_results = {}
        original_mode = self.performance_mode
        
        modes = ["fast", "balanced", "thorough"]
        
        for mode in modes:
            print(f"\n🔄 {mode.upper()} 모드 테스트 중...")
            
            # 모드 변경
            self.performance_mode = mode
            self._configure_performance_settings()
            self._apply_performance_settings()
            
            # 벤치마크 실행
            start_time = time.time()
            solutions = self.optimize(
                max_solutions=8,
                enable_visualization=False,
                save_results=False,
                max_combinations=None  # 모드별 자동 설정 사용
            )
            
            elapsed_time = time.time() - start_time
            
            # 결과 수집
            benchmark_results[mode] = {
                'execution_time': elapsed_time,
                'solutions_found': len(solutions),
                'best_fitness': solutions[0]['fitness'] if solutions else 0,
                'valid_solutions': sum(1 for s in solutions if s.get('constraint_valid', False)),
                'performance_report': self.optimizer.get_detailed_performance_report()
            }
            
            print(f"   ✅ {mode} 완료: {elapsed_time:.2f}초, {len(solutions)}개 솔루션")
        
        # 원래 모드로 복구
        self.performance_mode = original_mode
        self._configure_performance_settings()
        self._apply_performance_settings()
        
        # 벤치마크 결과 출력
        self._print_benchmark_results(benchmark_results)
        
        return benchmark_results
    
    def _print_benchmark_results(self, results: Dict[str, Any]):
        """벤치마크 결과 출력"""
        
        print(f"\n📊 성능 모드 벤치마크 결과")
        print("=" * 80)
        print(f"{'모드':<12} {'시간(초)':<10} {'솔루션수':<8} {'최고점수':<10} {'유효솔루션':<10} {'효율성':<10}")
        print("-" * 80)
        
        for mode, result in results.items():
            efficiency = result['solutions_found'] / result['execution_time'] if result['execution_time'] > 0 else 0
            
            print(f"{mode:<12} {result['execution_time']:<10.2f} {result['solutions_found']:<8} "
                  f"{result['best_fitness']:<10.1f} {result['valid_solutions']:<10} {efficiency:<10.2f}")
        
        print("=" * 80)
        
        # 추천 모드 결정
        best_balance = None
        best_score = 0
        
        for mode, result in results.items():
            # 균형 점수 = (품질 * 유효성) / 시간
            if result['execution_time'] > 0 and result['solutions_found'] > 0:
                balance_score = (result['best_fitness'] * result['valid_solutions']) / result['execution_time']
                if balance_score > best_score:
                    best_score = balance_score
                    best_balance = mode
        
        if best_balance:
            print(f"🎯 추천 모드: {best_balance.upper()} (균형 점수: {best_score:.1f})")
    
    def save_results(self, solutions: List[Dict[str, Any]], output_path: str = None):
        """최적화 결과를 JSON 파일로 저장"""
        
        if not solutions:
            print("💾 저장할 솔루션이 없습니다.")
            return
        
        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = f'improved_optimization_results_{timestamp}.json'
        
        # JSON 직렬화를 위한 데이터 정제
        serializable_results = []
        for solution in solutions:
            serializable_solution = {
                'fitness': solution['fitness'],
                'method': solution.get('method', ''),
                'code': solution.get('code', ''),
                'constraint_valid': solution.get('constraint_valid', False),
                'boundary_violations': solution.get('boundary_violations', False),
                'penalty_score': solution.get('penalty_score', 0),
                'generation': solution.get('generation', 0),
                'layout': [
                    {
                        'id': rect['id'],
                        'x': rect['x'],
                        'y': rect['y'],
                        'width': rect['width'],
                        'height': rect['height'],
                        'rotated': rect.get('rotated', False),
                        'building_type': rect.get('building_type', 'sub'),
                        'main_process_sequence': rect.get('main_process_sequence')
                    }
                    for rect in solution['layout']
                ]
            }
            serializable_results.append(serializable_solution)
        
        try:
            # 상세 정보 포함한 결과 저장
            result_data = {
                'optimization_info': {
                    'algorithm': 'improved_exhaustive_search',
                    'performance_mode': self.performance_mode,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'config_file': str(self.config_loader.config_path)
                },
                'site_info': {
                    'dimensions': self.config['site_dimensions'],
                    'total_processes': len(self.config['spaces']),
                    'main_processes': len(self.main_processes),
                    'sub_processes': len(self.sub_processes),
                    'fixed_zones': len(self.config.get('fixed_zones', []))
                },
                'performance_settings': self.perf_config,
                'solutions': serializable_results,
                'performance_report': self.optimizer.get_detailed_performance_report() if hasattr(self.optimizer, 'get_detailed_performance_report') else {}
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 향상된 결과 저장 완료: {output_path}")
            print(f"   📊 포함 정보: 솔루션 {len(serializable_results)}개 + 성능 보고서")
            
        except Exception as e:
            print(f"❌ 결과 저장 실패: {str(e)}")
    
    def _generate_performance_report(self, optimization_time: float, solutions: List[Dict[str, Any]]):
        """성능 보고서 생성"""
        
        if not hasattr(self.optimizer, 'get_detailed_performance_report'):
            return
        
        report = self.optimizer.get_detailed_performance_report()
        
        print(f"\n📈 성능 분석 보고서:")
        print(f"   ⚡ 실행 효율성: {report['efficiency_metrics']['combinations_per_second']:.1f} 조합/초")
        print(f"   🎯 성공률: {report['efficiency_metrics']['success_rate']*100:.1f}%")
        print(f"   📊 솔루션 품질 분포:")
        print(f"      └─ 평균 적합도: {report['solution_stats']['fitness_range']['avg']:.1f}점")
        print(f"      └─ 적합도 범위: {report['solution_stats']['fitness_range']['min']:.1f} ~ {report['solution_stats']['fitness_range']['max']:.1f}점")
        print(f"      └─ 제약 준수율: {report['solution_stats']['constraint_compliance_rate']*100:.1f}%")
        
        # 최적화 기법별 효과
        if 'optimization_techniques' in report:
            print(f"   🛠️ 최적화 기법 효과:")
            
            if 'early_pruning' in report['optimization_techniques']:
                pruning = report['optimization_techniques']['early_pruning']
                print(f"      └─ 조기 가지치기: {pruning['combinations_pruned']:,}개 제거 "
                      f"({pruning['efficiency_gain']*100:.1f}% 효율 향상)")
            
            if 'adaptive_sampling' in report['optimization_techniques']:
                sampling = report['optimization_techniques']['adaptive_sampling']
                print(f"      └─ 적응형 샘플링: {sampling['sample_size']:,}개 처리 "
                      f"(시드 포인트: {sampling['seed_positions']}개)")
        
        # 성능 등급 평가
        performance_grade = self._evaluate_performance_grade(report, optimization_time)
        print(f"   🏆 종합 성능 등급: {performance_grade}")
    
    def _evaluate_performance_grade(self, report: Dict[str, Any], optimization_time: float) -> str:
        """성능 등급 평가"""
        
        score = 0
        
        # 속도 점수 (30점)
        combinations_per_sec = report['efficiency_metrics']['combinations_per_second']
        if combinations_per_sec > 100:
            score += 30
        elif combinations_per_sec > 50:
            score += 25
        elif combinations_per_sec > 20:
            score += 20
        elif combinations_per_sec > 10:
            score += 15
        else:
            score += 10
        
        # 품질 점수 (30점)
        avg_fitness = report['solution_stats']['fitness_range']['avg']
        if avg_fitness > 900:
            score += 30
        elif avg_fitness > 800:
            score += 25
        elif avg_fitness > 700:
            score += 20
        elif avg_fitness > 600:
            score += 15
        else:
            score += 10
        
        # 성공률 점수 (25점)
        success_rate = report['efficiency_metrics']['success_rate']
        score += int(success_rate * 25)
        
        # 제약 준수율 점수 (15점)
        compliance_rate = report['solution_stats']['constraint_compliance_rate']
        score += int(compliance_rate * 15)
        
        # 등급 결정
        if score >= 90:
            return "S급 (탁월함)"
        elif score >= 80:
            return "A급 (우수함)"
        elif score >= 70:
            return "B급 (양호함)"
        elif score >= 60:
            return "C급 (보통함)"
        else:
            return "D급 (개선 필요)"
    
    def run_interactive_optimization(self):
        """대화형 최적화 실행 (개선된 버전)"""
        
        print("\n🎯 개선된 대화형 최적화 모드")
        print("=" * 50)
        
        while True:
            print("\n📋 최적화 옵션:")
            print("1. 빠른 최적화 (Fast) - 빠른 결과, 기본 품질")
            print("2. 균형 최적화 (Balanced) - 적당한 속도와 품질 (추천)")
            print("3. 철저한 최적화 (Thorough) - 느리지만 최고 품질")
            print("4. 성능 모드 벤치마크 - 모든 모드 비교 테스트")
            print("5. 커스텀 설정")
            print("6. 종료")
            
            choice = input("\n옵션을 선택하세요 (1-6): ").strip()
            
            if choice == '6':
                print("👋 최적화를 종료합니다.")
                break
            
            elif choice in ['1', '2', '3']:
                mode_map = {'1': 'fast', '2': 'balanced', '3': 'thorough'}
                selected_mode = mode_map[choice]
                
                print(f"\n🚀 {selected_mode.upper()} 모드로 최적화 시작...")
                
                # 모드 변경 및 실행
                original_mode = self.performance_mode
                self.performance_mode = selected_mode
                self._configure_performance_settings()
                self._apply_performance_settings()
                
                solutions = self.optimize()
                
                # 모드 복구
                self.performance_mode = original_mode
                self._configure_performance_settings()
                self._apply_performance_settings()
                
                if solutions:
                    save_choice = input("\n💾 결과를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
                    if save_choice == 'y':
                        filename = input("파일명 (기본값: 자동 생성): ").strip()
                        if filename:
                            self.save_results(solutions, filename)
                        else:
                            self.save_results(solutions)
            
            elif choice == '4':
                print("\n🏃 성능 벤치마크 실행 중...")
                benchmark_duration = input("각 모드별 테스트 시간(초, 기본값 30): ").strip()
                try:
                    duration = int(benchmark_duration) if benchmark_duration else 30
                except ValueError:
                    duration = 30
                
                benchmark_results = self.benchmark_performance_modes(duration)
                
                save_benchmark = input("\n💾 벤치마크 결과를 저장하시겠습니까? (y/n): ").strip().lower()
                if save_benchmark == 'y':
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    benchmark_file = f"performance_benchmark_{timestamp}.json"
                    try:
                        with open(benchmark_file, 'w', encoding='utf-8') as f:
                            json.dump(benchmark_results, f, indent=2, ensure_ascii=False, default=str)
                        print(f"📊 벤치마크 결과 저장: {benchmark_file}")
                    except Exception as e:
                        print(f"❌ 벤치마크 저장 실패: {str(e)}")
            
            elif choice == '5':
                print("\n🔧 커스텀 설정")
                try:
                    max_solutions = int(input("최대 솔루션 수 (기본값 8): ") or "8")
                    enable_viz = input("실시간 시각화 활성화? (y/n, 기본값 y): ").strip().lower() != 'n'
                    enable_early = input("조기 종료 활성화? (y/n, 기본값 y): ").strip().lower() != 'n'
                    
                    print(f"\n🎯 커스텀 설정으로 최적화 시작...")
                    solutions = self.optimize(
                        max_solutions=max_solutions,
                        enable_visualization=enable_viz,
                        enable_early_termination=enable_early
                    )
                    
                except ValueError:
                    print("⚠️ 잘못된 입력, 기본값으로 실행합니다.")
                    solutions = self.optimize()
            
            else:
                print("❌ 잘못된 선택입니다. 다시 선택해주세요.")
                continue
            
            # 계속 여부 확인
            if choice in ['1', '2', '3', '5']:
                continue_choice = input("\n🔄 다른 설정으로 최적화를 계속하시겠습니까? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    break


def main():
    """메인 함수"""
    
    print("🚀 개선된 공정 순서 기반 배치 최적화 시스템")
    print("=" * 60)
    
    # 명령줄 인수 처리
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python main_improved_optimizer.py <config_file.json> [성능모드]")
        print("  성능모드: fast, balanced, thorough (기본값: balanced)")
        print("\n예시:")
        print("  python main_improved_optimizer.py layout_config.json balanced")
        sys.exit(1)
    
    config_path = sys.argv[1]
    performance_mode = sys.argv[2] if len(sys.argv) > 2 else "balanced"
    
    # 설정 파일 존재 확인
    if not Path(config_path).exists():
        print(f"❌ 설정 파일을 찾을 수 없습니다: {config_path}")
        sys.exit(1)
    
    try:
        # 최적화 시스템 초기화
        optimizer = ImprovedProcessSequenceOptimizer(config_path, performance_mode)
        
        # 실행 모드 선택
        run_mode = input("\n실행 모드를 선택하세요:\n1. 자동 실행\n2. 대화형 모드\n선택 (1-2, 기본값 2): ").strip()
        
        if run_mode == '1':
            print("\n🤖 자동 실행 모드")
            solutions = optimizer.optimize()
            
            if solutions:
                print(f"\n🎉 최적화 완료! {len(solutions)}개 솔루션 발견")
                # optimizer.save_results(solutions)  250825_주석처리함
            else:
                print("\n😞 유효한 솔루션을 찾지 못했습니다.")
        
        else:
            # 대화형 최적화 실행
            optimizer.run_interactive_optimization()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 시스템 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()