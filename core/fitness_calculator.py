"""
적합도 계산기 모듈
SLP 가중치, 유해인자, 공정 순서 등을 종합하여 배치의 적합도를 평가합니다.
"""

from typing import Dict, List, Any, Tuple
from utils.geometry_utils import GeometryUtils


class FitnessCalculator:
    """다차원 적합도 평가 시스템"""
    
    def __init__(self, 
                 adjacency_weights: Dict[str, Dict[str, Any]], 
                 spaces: Dict[str, Any],
                 fixed_zones: List[Dict[str, Any]], 
                 site_width: int, 
                 site_height: int):
        """
        초기화
        
        Args:
            adjacency_weights: 인접성 가중치 정보
            spaces: 공정 정보
            fixed_zones: 고정 구역 정보
            site_width: 부지 너비
            site_height: 부지 높이
        """
        self.adjacency_weights = adjacency_weights
        self.spaces = spaces
        self.fixed_zones = fixed_zones
        self.site_width = site_width
        self.site_height = site_height
        self.geometry = GeometryUtils()
        
        # 가중치 설정 (중요도에 따른 점수 배율)
        self.weights = {
            'overlap_penalty': 2000,      # 겹침 (치명적)
            'boundary_penalty': 1000,     # 경계 위반 (치명적)
            'fixed_zone_penalty': 1500,   # 고정구역 침범 (치명적)
            'adjacency_score': 500,       # 인접성 점수 (중요)
            'sequence_bonus': 300,        # 공정 순서 준수 (중요)
            'hazard_penalty': 200,        # 유해인자 (보통)
            'utilization_bonus': 150,     # 부지 활용도 (보통)
            'compactness_bonus': 100,     # 컴팩트성 (낮음)
            'accessibility_bonus': 100    # 접근성 (낮음)
        }
        
        print(f"📊 적합도 계산기 초기화: 인접성 규칙 {len(adjacency_weights)}개")
    
    def calculate_fitness(self, layout: List[Dict[str, Any]]) -> float:
        """
        종합 적합도 점수 계산
        
        Args:
            layout: 배치된 공정 목록
        
        Returns:
            적합도 점수 (높을수록 좋음)
        """
        if not layout:
            return 0.0
        
        base_score = 1000.0
        
        # 1. 절대적 제약 위반 페널티 (치명적)
        overlap_penalty = self._calculate_overlap_penalty(layout)
        boundary_penalty = self._calculate_boundary_penalty(layout)
        fixed_zone_penalty = self._calculate_fixed_zone_penalty(layout)
        
        # 치명적 위반이 있으면 매우 낮은 점수 반환
        if overlap_penalty > 0 or boundary_penalty > 0 or fixed_zone_penalty > 0:
            return -(overlap_penalty * self.weights['overlap_penalty'] + 
                    boundary_penalty * self.weights['boundary_penalty'] +
                    fixed_zone_penalty * self.weights['fixed_zone_penalty'])
        
        # 2. 최적화 목표 점수들
        adjacency_score = self._calculate_adjacency_fitness(layout)
        sequence_bonus = self._calculate_sequence_compliance_bonus(layout)
        utilization_bonus = self._calculate_site_utilization_bonus(layout)
        compactness_bonus = self._calculate_compactness_bonus(layout)
        accessibility_bonus = self._calculate_accessibility_bonus(layout)
        
        # 3. 페널티 점수들
        hazard_penalty = self._calculate_hazard_penalty(layout)
        
        # 최종 점수 계산
        final_score = (
            base_score +
            adjacency_score * self.weights['adjacency_score'] / 1000 +
            sequence_bonus * self.weights['sequence_bonus'] / 1000 +
            utilization_bonus * self.weights['utilization_bonus'] / 1000 +
            compactness_bonus * self.weights['compactness_bonus'] / 1000 +
            accessibility_bonus * self.weights['accessibility_bonus'] / 1000 -
            hazard_penalty * self.weights['hazard_penalty'] / 1000
        )
        
        return max(0, final_score)
    
    def _calculate_overlap_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """공정 간 겹침 페널티 계산"""
        total_penalty = 0.0
        
        for i, rect1 in enumerate(layout):
            for rect2 in layout[i + 1:]:
                if self.geometry.rectangles_overlap(rect1, rect2):
                    overlap_area = self.geometry.calculate_overlap_area(rect1, rect2)
                    total_penalty += overlap_area
        
        return total_penalty
    
    def _calculate_boundary_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """부지 경계 위반 페널티 계산"""
        total_penalty = 0.0
        
        for rect in layout:
            # 경계를 벗어난 면적 계산
            x_overflow = max(0, rect['x'] + rect['width'] - self.site_width)
            y_overflow = max(0, rect['y'] + rect['height'] - self.site_height)
            x_underflow = max(0, -rect['x'])
            y_underflow = max(0, -rect['y'])
            
            # 벗어난 면적
            overflow_area = (
                x_overflow * rect['height'] +
                y_overflow * rect['width'] +
                x_underflow * rect['height'] +
                y_underflow * rect['width']
            )
            
            total_penalty += overflow_area
        
        return total_penalty
    
    def _calculate_fixed_zone_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """고정 구역 침범 페널티 계산"""
        total_penalty = 0.0
        
        for rect in layout:
            for fixed_zone in self.fixed_zones:
                if self.geometry.rectangles_overlap(rect, fixed_zone):
                    overlap_area = self.geometry.calculate_overlap_area(rect, fixed_zone)
                    total_penalty += overlap_area * 2  # 고정 구역 침범은 2배 페널티
        
        return total_penalty
    
    def _calculate_adjacency_fitness(self, layout: List[Dict[str, Any]]) -> float:
        """SLP 가중치 기반 인접성 적합도 계산"""
        total_score = 0.0
        
        for i, rect1 in enumerate(layout):
            for rect2 in layout[i + 1:]:
                distance = self.geometry.calculate_center_distance(rect1, rect2)
                
                # 인접성 가중치 조회
                weight_key1 = f"{rect1['id']}-{rect2['id']}"
                weight_key2 = f"{rect2['id']}-{rect1['id']}"
                
                weight_info = (self.adjacency_weights.get(weight_key1) or 
                              self.adjacency_weights.get(weight_key2) or 
                              {'weight': 2, 'preferred_gap': 100})
                
                weight = weight_info['weight']
                preferred_gap = weight_info.get('preferred_gap', 100)
                
                # SLP 가중치에 따른 점수 계산
                score = self.geometry.calculate_adjacency_score(
                    rect1, rect2, weight, preferred_gap
                )
                total_score += score
        
        return total_score
    
    def _calculate_sequence_compliance_bonus(self, layout: List[Dict[str, Any]]) -> float:
        """공정 순서 준수 보너스 계산"""
        
        # 주공정만 추출
        main_processes = [
            rect for rect in layout 
            if rect.get('building_type') == 'main'
        ]
        
        if len(main_processes) < 2:
            return 0.0
        
        # 순서대로 정렬
        main_processes.sort(key=lambda x: x.get('main_process_sequence', 999))
        
        total_bonus = 0.0
        
        # 순서대로 배치된 공정들 간의 연결성 평가
        for i in range(len(main_processes) - 1):
            current = main_processes[i]
            next_process = main_processes[i + 1]
            
            # 거리 기반 보너스 (가까울수록 좋음)
            distance = self.geometry.calculate_center_distance(current, next_process)
            proximity_bonus = max(0, 200 - distance / 5)  # 1000mm까지는 보너스
            
            # 방향성 보너스 (일관된 배치 방향)
            if i > 0:
                prev_process = main_processes[i - 1]
                direction_consistency = self._calculate_direction_consistency(
                    prev_process, current, next_process
                )
                proximity_bonus += direction_consistency * 50
            
            total_bonus += proximity_bonus
        
        return total_bonus
    
    def _calculate_direction_consistency(self, 
                                       rect1: Dict[str, Any], 
                                       rect2: Dict[str, Any], 
                                       rect3: Dict[str, Any]) -> float:
        """방향 일관성 계산 (0~1)"""
        
        # 첫 번째 연결의 방향
        dx1 = rect2['x'] - rect1['x']
        dy1 = rect2['y'] - rect1['y']
        
        # 두 번째 연결의 방향
        dx2 = rect3['x'] - rect2['x']
        dy2 = rect3['y'] - rect2['y']
        
        # 방향 벡터 정규화
        len1 = max(1, (dx1 ** 2 + dy1 ** 2) ** 0.5)
        len2 = max(1, (dx2 ** 2 + dy2 ** 2) ** 0.5)
        
        dx1_norm = dx1 / len1
        dy1_norm = dy1 / len1
        dx2_norm = dx2 / len2
        dy2_norm = dy2 / len2
        
        # 내적 (코사인 유사도)
        dot_product = dx1_norm * dx2_norm + dy1_norm * dy2_norm
        
        # -1~1을 0~1로 변환
        return (dot_product + 1) / 2
    
    def _calculate_site_utilization_bonus(self, layout: List[Dict[str, Any]]) -> float:
        """부지 활용도 보너스 계산"""
        
        utilization = self.geometry.calculate_utilization_ratio(
            layout, self.site_width, self.site_height
        )
        
        # 40~70% 활용률에서 최대 보너스
        if 0.4 <= utilization <= 0.7:
            return 200.0
        elif utilization < 0.4:
            return utilization / 0.4 * 200.0  # 선형 감소
        else:
            return max(0, 200 - (utilization - 0.7) * 400)  # 70% 초과시 페널티
    
    def _calculate_compactness_bonus(self, layout: List[Dict[str, Any]]) -> float:
        """컴팩트성 보너스 계산"""
        
        compactness = self.geometry.calculate_compactness(layout)
        
        # 컴팩트성이 높을수록 보너스 (최대 150점)
        return compactness * 150
    
    def _calculate_accessibility_bonus(self, layout: List[Dict[str, Any]]) -> float:
        """접근성 보너스 계산"""
        total_bonus = 0.0
        
        # 고정 구역(도로, 출입구 등)과의 접근성 평가
        for rect in layout:
            min_access_distance = float('inf')
            
            for fixed_zone in self.fixed_zones:
                if 'road' in fixed_zone.get('name', '').lower():
                    distance = self.geometry.calculate_edge_distance(rect, fixed_zone)
                    min_access_distance = min(min_access_distance, distance)
            
            if min_access_distance != float('inf'):
                # 5m 이내면 최대 보너스, 멀어질수록 감소
                access_bonus = max(0, 100 - min_access_distance * 20)
                total_bonus += access_bonus
        
        return total_bonus
    
    def _calculate_hazard_penalty(self, layout: List[Dict[str, Any]]) -> float:
        """유해인자 기반 페널티 계산"""
        total_penalty = 0.0
        
        # spaces에서 유해인자 정보 가져오기
        hazard_info = {}
        for space_id, space_data in self.spaces.items():
            if 'hazard_factors' in space_data:
                hazard_info[space_id] = space_data['hazard_factors']
        
        # 유해인자 조합별 최소 거리 요구사항 (m 단위)
        hazard_distance_requirements = {
            ('화재', '폭발'): 10.0,      # 화재와 폭발 위험 공정 간 최소 10m
            ('화재', '독성'): 8.0,       # 화재와 독성 물질 간 최소 8m
            ('폭발', '독성'): 12.0,      # 폭발과 독성 물질 간 최소 12m
            ('화재', '화재'): 6.0,       # 화재 위험 공정 간 최소 6m
            ('폭발', '폭발'): 15.0,      # 폭발 위험 공정 간 최소 15m
            ('독성', '독성'): 5.0        # 독성 물질 간 최소 5m
        }
        
        # 모든 공정 쌍에 대해 유해인자 검사
        for i, rect1 in enumerate(layout):
            id1 = rect1['id']
            hazards1 = hazard_info.get(id1, [])
            
            for rect2 in layout[i + 1:]:
                id2 = rect2['id']
                hazards2 = hazard_info.get(id2, [])
                
                if hazards1 and hazards2:
                    # 유해인자 조합 확인
                    for hazard1 in hazards1:
                        for hazard2 in hazards2:
                            # 양방향으로 확인
                            combo1 = (hazard1, hazard2)
                            combo2 = (hazard2, hazard1)
                            
                            required_distance = (hazard_distance_requirements.get(combo1) or 
                                               hazard_distance_requirements.get(combo2) or 0)
                            
                            if required_distance > 0:
                                actual_distance = self.geometry.calculate_edge_distance(rect1, rect2)
                                
                                if actual_distance < required_distance:
                                    violation = required_distance - actual_distance
                                    total_penalty += violation * 2  # 거리 위반에 비례한 페널티
        
        return total_penalty
    
    def get_fitness_breakdown(self, layout: List[Dict[str, Any]]) -> Dict[str, float]:
        """적합도 점수의 상세 분석 결과 반환"""
        
        if not layout:
            return {
                'total_score': 0.0,
                'base_score': 0.0,
                'penalties': {},
                'bonuses': {},
                'violations': []
            }
        
        base_score = 1000.0
        
        # 페널티 계산
        overlap_penalty = self._calculate_overlap_penalty(layout)
        boundary_penalty = self._calculate_boundary_penalty(layout)
        fixed_zone_penalty = self._calculate_fixed_zone_penalty(layout)
        hazard_penalty = self._calculate_hazard_penalty(layout)
        
        # 보너스 계산
        adjacency_score = self._calculate_adjacency_fitness(layout)
        sequence_bonus = self._calculate_sequence_compliance_bonus(layout)
        utilization_bonus = self._calculate_site_utilization_bonus(layout)
        compactness_bonus = self._calculate_compactness_bonus(layout)
        accessibility_bonus = self._calculate_accessibility_bonus(layout)
        
        # 위반사항 확인
        violations = []
        if overlap_penalty > 0:
            violations.append("공정 간 겹침")
        if boundary_penalty > 0:
            violations.append("부지 경계 위반")
        if fixed_zone_penalty > 0:
            violations.append("고정 구역 침범")
        if hazard_penalty > 0:
            violations.append("유해인자 최소거리 위반")
        
        # 치명적 위반이 있으면 총점 음수
        if violations:
            total_score = -(overlap_penalty * self.weights['overlap_penalty'] + 
                           boundary_penalty * self.weights['boundary_penalty'] +
                           fixed_zone_penalty * self.weights['fixed_zone_penalty'])
        else:
            total_score = (
                base_score +
                adjacency_score * self.weights['adjacency_score'] / 1000 +
                sequence_bonus * self.weights['sequence_bonus'] / 1000 +
                utilization_bonus * self.weights['utilization_bonus'] / 1000 +
                compactness_bonus * self.weights['compactness_bonus'] / 1000 +
                accessibility_bonus * self.weights['accessibility_bonus'] / 1000 -
                hazard_penalty * self.weights['hazard_penalty'] / 1000
            )
        
        return {
            'total_score': max(0, total_score),
            'base_score': base_score,
            'penalties': {
                'overlap': overlap_penalty,
                'boundary': boundary_penalty,
                'fixed_zone': fixed_zone_penalty,
                'hazard': hazard_penalty
            },
            'bonuses': {
                'adjacency': adjacency_score,
                'sequence': sequence_bonus,
                'utilization': utilization_bonus,
                'compactness': compactness_bonus,
                'accessibility': accessibility_bonus
            },
            'violations': violations,
            'weighted_scores': {
                'adjacency_weighted': adjacency_score * self.weights['adjacency_score'] / 1000,
                'sequence_weighted': sequence_bonus * self.weights['sequence_bonus'] / 1000,
                'utilization_weighted': utilization_bonus * self.weights['utilization_bonus'] / 1000,
                'compactness_weighted': compactness_bonus * self.weights['compactness_bonus'] / 1000,
                'accessibility_weighted': accessibility_bonus * self.weights['accessibility_bonus'] / 1000,
                'hazard_weighted': -hazard_penalty * self.weights['hazard_penalty'] / 1000
            }
        }
    
    def compare_layouts(self, layout1: List[Dict[str, Any]], layout2: List[Dict[str, Any]]) -> Dict[str, Any]:
        """두 배치의 적합도 비교"""
        
        breakdown1 = self.get_fitness_breakdown(layout1)
        breakdown2 = self.get_fitness_breakdown(layout2)
        
        comparison = {
            'layout1_score': breakdown1['total_score'],
            'layout2_score': breakdown2['total_score'],
            'winner': 'layout1' if breakdown1['total_score'] > breakdown2['total_score'] else 'layout2',
            'score_difference': abs(breakdown1['total_score'] - breakdown2['total_score']),
            'category_comparison': {}
        }
        
        # 카테고리별 비교
        for category in ['adjacency', 'sequence', 'utilization', 'compactness', 'accessibility']:
            score1 = breakdown1['bonuses'][category]
            score2 = breakdown2['bonuses'][category]
            comparison['category_comparison'][category] = {
                'layout1': score1,
                'layout2': score2,
                'difference': score2 - score1,
                'winner': 'layout1' if score1 > score2 else 'layout2'
            }
        
        return comparison
    
    def suggest_improvements(self, layout: List[Dict[str, Any]]) -> List[str]:
        """배치 개선 제안사항 생성"""
        
        breakdown = self.get_fitness_breakdown(layout)
        suggestions = []
        
        # 위반사항 기반 제안
        if breakdown['violations']:
            for violation in breakdown['violations']:
                if violation == "공정 간 겹침":
                    suggestions.append("겹치는 공정들의 위치를 조정하세요")
                elif violation == "부지 경계 위반":
                    suggestions.append("부지 경계를 벗어난 공정들을 내부로 이동하세요")
                elif violation == "고정 구역 침범":
                    suggestions.append("고정 구역(도로, 주차장 등)을 피해 공정을 재배치하세요")
                elif violation == "유해인자 최소거리 위반":
                    suggestions.append("유해인자가 있는 공정들 간의 거리를 늘리세요")
        
        # 점수 기반 제안
        bonuses = breakdown['bonuses']
        
        if bonuses['adjacency'] < 100:
            suggestions.append("SLP 가중치가 높은 공정들을 더 가깝게 배치하세요")
        
        if bonuses['sequence'] < 150:
            suggestions.append("주공정들 간의 연결성을 개선하세요 (일관된 방향으로 배치)")
        
        if bonuses['utilization'] < 120:
            suggestions.append("부지 활용률을 개선하세요 (40-70%가 최적)")
        
        if bonuses['compactness'] < 80:
            suggestions.append("공정들을 더 집약적으로 배치하여 컴팩트성을 높이세요")
        
        if bonuses['accessibility'] < 60:
            suggestions.append("도로나 출입구에 대한 접근성을 개선하세요")
        
        return suggestions
    
    def validate_fitness_requirements(self, layout: List[Dict[str, Any]]) -> Dict[str, bool]:
        """적합도 요구사항 검증"""
        
        breakdown = self.get_fitness_breakdown(layout)
        
        requirements = {
            'no_overlaps': breakdown['penalties']['overlap'] == 0,
            'within_boundaries': breakdown['penalties']['boundary'] == 0,
            'avoid_fixed_zones': breakdown['penalties']['fixed_zone'] == 0,
            'hazard_distances_ok': breakdown['penalties']['hazard'] == 0,
            'good_adjacency': breakdown['bonuses']['adjacency'] >= 100,
            'sequence_compliance': breakdown['bonuses']['sequence'] >= 150,
            'acceptable_utilization': breakdown['bonuses']['utilization'] >= 120,
            'good_compactness': breakdown['bonuses']['compactness'] >= 80,
            'good_accessibility': breakdown['bonuses']['accessibility'] >= 60
        }
        
        requirements['all_critical_met'] = (
            requirements['no_overlaps'] and 
            requirements['within_boundaries'] and 
            requirements['avoid_fixed_zones'] and 
            requirements['hazard_distances_ok']
        )
        
        requirements['all_requirements_met'] = all(requirements.values())
        
        return requirements
    
    def print_fitness_report(self, layout: List[Dict[str, Any]]):
        """적합도 분석 리포트 출력"""
        
        breakdown = self.get_fitness_breakdown(layout)
        
        print(f"\n📊 적합도 분석 리포트")
        print(f"=" * 50)
        print(f"🏆 총점: {breakdown['total_score']:.2f}")
        print(f"📏 기본점수: {breakdown['base_score']:.2f}")
        
        if breakdown['violations']:
            print(f"\n❌ 위반사항:")
            for violation in breakdown['violations']:
                print(f"   - {violation}")
        else:
            print(f"\n✅ 모든 제약 조건 만족")
        
        print(f"\n📈 보너스 점수:")
        bonuses = breakdown['bonuses']
        weighted = breakdown['weighted_scores']
        
        print(f"   🔗 인접성: {bonuses['adjacency']:.1f} (가중: {weighted['adjacency_weighted']:.1f})")
        print(f"   📋 순서준수: {bonuses['sequence']:.1f} (가중: {weighted['sequence_weighted']:.1f})")
        print(f"   📐 활용률: {bonuses['utilization']:.1f} (가중: {weighted['utilization_weighted']:.1f})")
        print(f"   📦 컴팩트성: {bonuses['compactness']:.1f} (가중: {weighted['compactness_weighted']:.1f})")
        print(f"   🚪 접근성: {bonuses['accessibility']:.1f} (가중: {weighted['accessibility_weighted']:.1f})")
        
        print(f"\n📉 페널티 점수:")
        penalties = breakdown['penalties']
        
        if penalties['overlap'] > 0:
            print(f"   ❌ 겹침: -{penalties['overlap']:.1f}")
        if penalties['boundary'] > 0:
            print(f"   ❌ 경계위반: -{penalties['boundary']:.1f}")
        if penalties['fixed_zone'] > 0:
            print(f"   ❌ 고정구역 침범: -{penalties['fixed_zone']:.1f}")
        if penalties['hazard'] > 0:
            print(f"   ❌ 유해인자: -{penalties['hazard']:.1f} (가중: {weighted['hazard_weighted']:.1f})")
        
        # 개선 제안
        suggestions = self.suggest_improvements(layout)
        if suggestions:
            print(f"\n💡 개선 제안:")
            for suggestion in suggestions:
                print(f"   - {suggestion}")


if __name__ == "__main__":
    # 테스트 실행
    print("🧪 FitnessCalculator 테스트")
    
    # 테스트 데이터 준비
    from core.config_loader import ConfigLoader, create_sample_config
    from core.process_classifier import ProcessClassifier
    from core.layout_generator import SequenceLayoutGenerator
    
    try:
        # 샘플 설정 생성 및 로드
        create_sample_config('test_fitness_config.json')
        loader = ConfigLoader('test_fitness_config.json')
        config = loader.load_config()
        
        # 공정 분류
        classifier = ProcessClassifier(config)
        main_processes, sub_processes = classifier.classify_processes()
        
        # 배치 생성
        generator = SequenceLayoutGenerator(
            site_width=config['site_dimensions']['width'],
            site_height=config['site_dimensions']['height'],
            fixed_zones=loader.get_fixed_zones()
        )
        
        layouts = generator.generate_main_layout_combinations(main_processes)
        if layouts:
            test_layout = layouts[0]
            complete_layout = generator.place_sub_processes_optimally(
                test_layout, sub_processes, config.get('adjacency_weights', {})
            )
            
            # 적합도 계산기 테스트
            fitness_calc = FitnessCalculator(
                adjacency_weights=config.get('adjacency_weights', {}),
                spaces=config['spaces'],
                fixed_zones=loader.get_fixed_zones(),
                site_width=config['site_dimensions']['width'],
                site_height=config['site_dimensions']['height']
            )
            
            # 적합도 계산
            fitness_score = fitness_calc.calculate_fitness(complete_layout)
            print(f"🎯 적합도 점수: {fitness_score:.2f}")
            
            # 상세 분석
            fitness_calc.print_fitness_report(complete_layout)
            
            # 요구사항 검증
            requirements = fitness_calc.validate_fitness_requirements(complete_layout)
            print(f"\n✅ 모든 요구사항 충족: {requirements['all_requirements_met']}")
            print(f"✅ 필수 요구사항 충족: {requirements['all_critical_met']}")
            
        else:
            print("❌ 테스트할 배치를 생성하지 못했습니다")
        
        print("\n✅ 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()