#!/usr/bin/env python3
"""
공정 순서 기반 배치 최적화 메인 실행 스크립트
JSON 파일을 읽어들여서 main_process_sequence 순서에 따라 공장 배치를 최적화합니다.
"""

import json
import time
import sys
from pathlib import Path

# 로컬 모듈 임포트 (직접 임포트 방식으로 변경)
try:
    from core.config_loader import ConfigLoader
    from core.process_classifier import ProcessClassifier
    from core.layout_generator import SequenceLayoutGenerator
    from core.fitness_calculator import FitnessCalculator
    from core.constraint_handler import ConstraintHandler
    from optimization.exhaustive_search import ExhaustiveSearchOptimizer
except ImportError as e:
    print(f"❌ 필수 모듈 임포트 오류: {e}")
    print("   프로젝트 구조를 확인하고 모든 필요한 파일이 있는지 확인해주세요.")
    sys.exit(1)

# 선택적 모듈 임포트 (없어도 기본 기능 동작)
try:
    from optimization.genetic_algorithm import GeneticAlgorithmOptimizer
    GENETIC_AVAILABLE = True
except ImportError:
    print("⚠️ genetic_algorithm 모듈이 없습니다. 전수 탐색만 사용 가능합니다.")
    GeneticAlgorithmOptimizer = None
    GENETIC_AVAILABLE = False

try:
    from optimization.hybrid_optimizer import HybridOptimizer
    HYBRID_AVAILABLE = True
except ImportError:
    print("⚠️ hybrid_optimizer 모듈이 없습니다. 전수 탐색만 사용 가능합니다.")
    HybridOptimizer = None
    HYBRID_AVAILABLE = False

# 시각화 완전 비활성화 (matplotlib 문제 회피)
VISUALIZATION_AVAILABLE = False
print("⚠️ 시각화가 비활성화되었습니다. (성능 향상)")

class RealtimeVisualizer:
    def __init__(self, *args, **kwargs): 
        pass
    def start_optimization(self): 
        print("📺 시각화 비활성화 모드 - 콘솔 진행률만 표시됩니다.")
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
        else:
            print("❌ 생성된 솔루션이 없습니다.")

try:
    from utils.geometry_utils import GeometryUtils
except ImportError:
    print("⚠️ geometry_utils 모듈이 없습니다.")
    sys.exit(1)


class ProcessSequenceOptimizer:
    """공정 순서 기반 배치 최적화 메인 컨트롤러"""
    
    def __init__(self, config_path: str):
        """
        초기화
        
        Args:
            config_path: JSON 설정 파일 경로
        """
        print("🏭 공정 순서 기반 배치 최적화 시스템 초기화 중...")
        
        # 1. 설정 파일 로드
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load_config()
        
        # 2. 공정 분류 및 검증
        self.process_classifier = ProcessClassifier(self.config)
        self.main_processes, self.sub_processes = self.process_classifier.classify_processes()
        
        # 3. 핵심 모듈 초기화
        self.layout_generator = SequenceLayoutGenerator(
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
        
        # 4. 최적화 엔진 초기화 (사용 가능한 것만)
        self.optimizers = {
            'exhaustive': ExhaustiveSearchOptimizer(
                self.layout_generator, 
                self.fitness_calculator, 
                self.constraint_handler
            )
        }
        
        # 선택적 최적화 엔진 추가
        if GENETIC_AVAILABLE:
            self.optimizers['genetic'] = GeneticAlgorithmOptimizer(
                self.layout_generator, 
                self.fitness_calculator, 
                self.constraint_handler
            )
        
        if HYBRID_AVAILABLE:
            self.optimizers['hybrid'] = HybridOptimizer(
                self.layout_generator, 
                self.fitness_calculator, 
                self.constraint_handler
            )
        
        # 5. 시각화 모듈 초기화 (가능한 경우에만)
        if VISUALIZATION_AVAILABLE:
            self.realtime_visualizer = RealtimeVisualizer(
                site_width=self.config['site_dimensions']['width'],
                site_height=self.config['site_dimensions']['height']
            )
            
            self.result_visualizer = ResultVisualizer(
                site_width=self.config['site_dimensions']['width'],
                site_height=self.config['site_dimensions']['height']
            )
        else:
            # 대체 시각화기 (콘솔 출력)
            self.realtime_visualizer = RealtimeVisualizer()
            self.result_visualizer = ResultVisualizer()
        
        print("✅ 시스템 초기화 완료!")
        self._print_system_info()
        self._print_available_algorithms()
    
    def _print_available_algorithms(self):
        """사용 가능한 알고리즘 정보 출력"""
        print(f"\n🔧 사용 가능한 최적화 알고리즘:")
        print(f"   ✅ 전수 탐색 (Exhaustive Search)")
        
        if GENETIC_AVAILABLE:
            print(f"   ✅ 유전 알고리즘 (Genetic Algorithm)")
        else:
            print(f"   ❌ 유전 알고리즘 - 모듈 없음")
            
        if HYBRID_AVAILABLE:
            print(f"   ✅ 하이브리드 (Hybrid)")
        else:
            print(f"   ❌ 하이브리드 - 모듈 없음")
    
    def _print_system_info(self):
        """시스템 정보 출력"""
        print("\n📊 시스템 정보:")
        print(f"   📐 부지 크기: {self.config['site_dimensions']['width']}×{self.config['site_dimensions']['height']}mm")
        print(f"   🏭 주공정: {len(self.main_processes)}개")
        print(f"   🔧 부공정: {len(self.sub_processes)}개")
        print(f"   🚧 고정구역: {len(self.config.get('fixed_zones', []))}개")
        print(f"   🔗 인접성 규칙: {len(self.config.get('adjacency_weights', {}))}개")
        
        # 주공정 순서 출력
        if self.main_processes:
            print("\n📋 주공정 배치 순서:")
            for i, process in enumerate(self.main_processes, 1):
                sequence = process.get('main_process_sequence', 'N/A')
                print(f"   {i}. {process['id']} (순서: {sequence}) - {process['width']}×{process['height']}mm")
    
    def optimize(self, algorithm='hybrid', **kwargs):
        """
        최적화 실행
        
        Args:
            algorithm: 최적화 알고리즘 ('exhaustive', 'genetic', 'hybrid')
            **kwargs: 알고리즘별 추가 파라미터
        
        Returns:
            최적화 결과 (상위 8개 솔루션)
        """
        print(f"\n🚀 {algorithm.upper()} 알고리즘으로 최적화 시작...")
        start_time = time.time()
        
        # 선택된 알고리즘으로 최적화 실행
        if algorithm not in self.optimizers:
            raise ValueError(f"지원되지 않는 알고리즘: {algorithm}")
        
        optimizer = self.optimizers[algorithm]
        
        # 실시간 시각화 시작
        self.realtime_visualizer.start_optimization()
        
        try:
            # 최적화 실행
            # 🚀 빠른 테스트 모드 옵션 추가
            test_mode = kwargs.get('test_mode', False)
            max_combinations = 1 if test_mode else None  # 테스트 모드 시 20개만 처리
            
            if test_mode:
                print("⚡ 빠른 테스트 모드 활성화: 20개 조합만 처리합니다.")
            
            solutions = optimizer.optimize(
                self.main_processes, 
                self.sub_processes, 
                visualizer=self.realtime_visualizer,
                max_combinations=max_combinations,
                **kwargs
            )
            
            end_time = time.time()
            optimization_time = end_time - start_time
            
            print(f"✅ 최적화 완료! 소요시간: {optimization_time:.1f}초")
            print(f"📈 발견된 유효한 솔루션: {len(solutions)}개")
            
            if solutions:
                # 최고 점수 출력
                best_fitness = max(solution['fitness'] for solution in solutions)
                print(f"🏆 최고 적합도 점수: {best_fitness:.2f}")
                
                # 상위 8개 솔루션 선택
                top_solutions = sorted(solutions, key=lambda x: x['fitness'], reverse=True)[:8]
                
                # 결과 시각화
                self.result_visualizer.show_results(top_solutions)
                
                return top_solutions
            else:
                print("❌ 유효한 솔루션을 찾지 못했습니다.")
                return []
                
        except Exception as e:
            print(f"❌ 최적화 중 오류 발생: {str(e)}")
            return []
        
        finally:
            # 실시간 시각화 종료
            self.realtime_visualizer.stop_optimization()
    
    def save_results(self, solutions, output_path='optimization_results.json'):
        """
        최적화 결과를 JSON 파일로 저장
        
        Args:
            solutions: 최적화 결과 솔루션들
            output_path: 출력 파일 경로
        """
        if not solutions:
            print("저장할 솔루션이 없습니다.")
            return
        
        # JSON 직렬화를 위한 데이터 정제
        serializable_results = []
        for solution in solutions:
            serializable_solution = {
                'fitness': solution['fitness'],
                'method': solution['method'],
                'code': solution.get('code', ''),
                'layout': [
                    {
                        'id': rect['id'],
                        'x': rect['x'],
                        'y': rect['y'],
                        'width': rect['width'],
                        'height': rect['height'],
                        'rotated': rect.get('rotated', False)
                    }
                    for rect in solution['layout']
                ]
            }
            serializable_results.append(serializable_solution)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'optimization_results': serializable_results,
                    'config_summary': {
                        'site_dimensions': self.config['site_dimensions'],
                        'total_processes': len(self.config['spaces']),
                        'main_processes': len(self.main_processes),
                        'sub_processes': len(self.sub_processes)
                    },
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, indent=2, ensure_ascii=False)
            
            print(f"💾 결과 저장 완료: {output_path}")
            
        except Exception as e:
            print(f"❌ 결과 저장 실패: {str(e)}")
    
    def run_interactive_optimization(self):
        """대화형 최적화 실행"""
        print("\n🎯 대화형 최적화 모드")
        print("=" * 50)
        
        while True:
            print("\n선택 가능한 최적화 알고리즘:")
            print("1. 전수 탐색 (Exhaustive Search) - 정확하지만 느림")
            
            if GENETIC_AVAILABLE:
                print("2. 유전 알고리즘 (Genetic Algorithm) - 균형적")
            else:
                print("2. 유전 알고리즘 - 사용 불가 (모듈 없음)")
            
            if HYBRID_AVAILABLE:
                print("3. 하이브리드 (Hybrid) - 최고 품질 (권장)")
            else:
                print("3. 하이브리드 - 사용 불가 (모듈 없음)")
            
            print("4. 종료")
            
            choice = input("\n알고리즘을 선택하세요 (1-4): ").strip()
            
            if choice == '4':
                print("👋 최적화를 종료합니다.")
                break
            
            algorithm_map = {'1': 'exhaustive'}
            
            if GENETIC_AVAILABLE:
                algorithm_map['2'] = 'genetic'
            if HYBRID_AVAILABLE:
                algorithm_map['3'] = 'hybrid'
            
            if choice not in algorithm_map:
                if choice == '2' and not GENETIC_AVAILABLE:
                    print("❌ 유전 알고리즘 모듈이 없습니다. 다른 알고리즘을 선택해주세요.")
                elif choice == '3' and not HYBRID_AVAILABLE:
                    print("❌ 하이브리드 모듈이 없습니다. 다른 알고리즘을 선택해주세요.")
                else:
                    print("❌ 잘못된 선택입니다. 다시 선택해주세요.")
                continue
            
            algorithm = algorithm_map[choice]
            
            # 알고리즘별 파라미터 설정
            kwargs = {}
            if algorithm == 'genetic' and GENETIC_AVAILABLE:
                try:
                    generations = int(input("세대 수 (기본값: 100): ") or "100")
                    population_size = int(input("개체 수 (기본값: 50): ") or "50")
                    kwargs = {'generations': generations, 'population_size': population_size}
                except ValueError:
                    print("⚠️ 잘못된 입력, 기본값 사용")
                    kwargs = {'generations': 100, 'population_size': 50}
            
            # 최적화 실행
            solutions = self.optimize(algorithm, **kwargs)
            
            if solutions:
                # 결과 저장 여부 확인
                save_choice = input("\n결과를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
                if save_choice == 'y':
                    filename = input("파일명 (기본값: optimization_results.json): ").strip()
                    if not filename:
                        filename = "optimization_results.json"
                    self.save_results(solutions, filename)
                
                # 계속 여부 확인
                continue_choice = input("\n다른 알고리즘으로 최적화를 계속하시겠습니까? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    break
            else:
                print("⚠️ 최적화가 실패했습니다. 설정을 확인해주세요.")


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python main_process_optimizer.py <config_file.json>")
        print("예시: python main_process_optimizer.py layout_config.json")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    # 설정 파일 존재 확인
    if not Path(config_path).exists():
        print(f"❌ 설정 파일을 찾을 수 없습니다: {config_path}")
        sys.exit(1)
    
    try:
        # 최적화 시스템 초기화
        optimizer = ProcessSequenceOptimizer(config_path)
        
        # 대화형 최적화 실행
        optimizer.run_interactive_optimization()
        
    except Exception as e:
        print(f"❌ 시스템 오류: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    
    # 명령줄 인수 확인
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'layout_config.json'
    test_mode = '--test' in sys.argv or '-t' in sys.argv
    
    print(f"📂 설정 파일: {config_file}")
    if test_mode:
        print("⚡ 테스트 모드 활성화")
    
    optimizer = ProcessSequenceOptimizer(config_file)
    solutions = optimizer.optimize(
        algorithm='exhaustive',
        test_mode=test_mode  # 🚀 이 부분이 핵심!
    )