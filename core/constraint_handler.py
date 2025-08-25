"""
제약 조건 처리기 모듈
배치의 유효성을 검증하고 제약 조건 위반을 확인합니다.
"""

from typing import Dict, List, Any, Tuple, Optional
from utils.geometry_utils import GeometryUtils


class ConstraintHandler:
    """제약 조건 검사 및 처리 클래스"""
    
    def __init__(self, 
                 site_width: int, 
                 site_height: int, 
                 fixed_zones: List[Dict[str, Any]], 
                 hazard_factors: Dict[str, List[str]] = None):
        """
        초기화
        
        Args:
            site_width: 부지 너비
            site_height: 부지 높이
            fixed_zones: 고정 구역 목록
            hazard_factors: 유해인자 정보
        """
        self.site_width = site_width
        self.site_height = site_height
        self.fixed_zones = fixed_zones or []
        self.hazard_factors = hazard_factors or {}
        self.geometry = GeometryUtils()
        
        # 유해인자별 최소 거리 요구사항 (m 단위)
        self.hazard_distance_requirements = {
            ('화재', '폭발'): 10.0,
            ('화재', '독성'): 8.0,
            ('폭발', '독성'): 12.0,
            ('화재', '화재'): 6.0,
            ('폭발', '폭발'): 15.0,
            ('독성', '독성'): 5.0,
            ('고압', '화재'): 10.0,
            ('고압', '폭발'): 12.0,
            ('방사능', '화재'): 20.0,
            ('방사능', '폭발'): 25.0,
            ('방사능', '독성'): 15.0
        }
        
        print(f"🛡️  제약 조건 처리기 초기화: 고정구역 {len(self.fixed_zones)}개, 유해인자 {len(self.hazard_factors)}개")
    
    def is_valid(self, layout: List[Dict[str, Any]]) -> bool:
        """
        배치의 전반적 유효성 검사
        
        Args:
            layout: 검사할 배치
        
        Returns:
            유효성 여부 (모든 제약 조건을 만족하면 True)
        """
        if not layout:
            return False
        
        # 필수 제약 조건들 검사
        constraints = [
            self.check_no_overlaps(layout),
            self.check_within_boundaries(layout),
            self.check_no_fixed_zone_violations(layout),
            self.check_hazard_distances(layout)
        ]
        
        return all(constraint['is_valid'] for constraint in constraints)
    
    def validate_layout(self, layout: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        배치의 상세 유효성 검사 결과 반환
        
        Args:
            layout: 검사할 배치
        
        Returns:
            상세 검사 결과
        """
        validation_result = {
            'is_valid': True,
            'violations': [],
            'warnings': [],
            'constraints': {},
            'statistics': {}
        }
        
        if not layout:
            validation_result['is_valid'] = False
            validation_result['violations'].append("배치가 비어있습니다")
            return validation_result
        
        # 각 제약 조건 검사
        overlap_check = self.check_no_overlaps(layout)
        boundary_check = self.check_within_boundaries(layout)
        fixed_zone_check = self.check_no_fixed_zone_violations(layout)
        hazard_check = self.check_hazard_distances(layout)
        sequence_check = self.check_main_process_sequence(layout)
        
        # 결과 통합
        constraint_checks = {
            'overlaps': overlap_check,
            'boundaries': boundary_check,
            'fixed_zones': fixed_zone_check,
            'hazard_distances': hazard_check,
            'sequence': sequence_check
        }
        
        validation_result['constraints'] = constraint_checks
        
        # 위반사항 수집
        for constraint_name, check_result in constraint_checks.items():
            if not check_result['is_valid']:
                validation_result['is_valid'] = False
                validation_result['violations'].extend(check_result['violations'])
            
            if check_result.get('warnings'):
                validation_result['warnings'].extend(check_result['warnings'])
        
        # 통계 정보
        validation_result['statistics'] = {
            'process_count': len(layout),
            'main_processes': len([r for r in layout if r.get('building_type') == 'main']),
            'sub_processes': len([r for r in layout if r.get('building_type') == 'sub']),
            'total_area': sum(r['width'] * r['height'] for r in layout),
            'utilization_ratio': self.geometry.calculate_utilization_ratio(
                layout, self.site_width, self.site_height
            )
        }
        
        return validation_result
    
    def check_no_overlaps(self, layout: List[Dict[str, Any]]) -> Dict[str, Any]:
        """공정 간 겹침 검사"""
        
        result = {
            'is_valid': True,
            'violations': [],
            'overlapping_pairs': []
        }
        
        for i, rect1 in enumerate(layout):
            for rect2 in layout[i + 1:]:
                if self.geometry.rectangles_overlap(rect1, rect2):
                    result['is_valid'] = False
                    
                    overlap_area = self.geometry.calculate_overlap_area(rect1, rect2)
                    violation_msg = f"'{rect1['id']}'와 '{rect2['id']}'가 겹침 (면적: {overlap_area:.0f}mm²)"
                    result['violations'].append(violation_msg)
                    result['overlapping_pairs'].append((rect1['id'], rect2['id'], overlap_area))
        
        return result
    
    def check_within_boundaries(self, layout: List[Dict[str, Any]]) -> Dict[str, Any]:
        """부지 경계 내 배치 검사"""
        
        result = {
            'is_valid': True,
            'violations': [],
            'boundary_violations': []
        }
        
        for rect in layout:
            violations = []
            
            if rect['x'] < 0:
                violations.append(f"왼쪽 경계 위반: x={rect['x']}")
            if rect['y'] < 0:
                violations.append(f"위쪽 경계 위반: y={rect['y']}")
            if rect['x'] + rect['width'] > self.site_width:
                violations.append(f"오른쪽 경계 위반: x+w={rect['x'] + rect['width']} > {self.site_width}")
            if rect['y'] + rect['height'] > self.site_height:
                violations.append(f"아래쪽 경계 위반: y+h={rect['y'] + rect['height']} > {self.site_height}")
            
            if violations:
                result['is_valid'] = False
                result['violations'].append(f"'{rect['id']}' 경계 위반: {', '.join(violations)}")
                result['boundary_violations'].append({
                    'process_id': rect['id'],
                    'violations': violations
                })
        
        return result
    
    def check_no_fixed_zone_violations(self, layout: List[Dict[str, Any]]) -> Dict[str, Any]:
        """고정 구역 침범 검사"""
        
        result = {
            'is_valid': True,
            'violations': [],
            'zone_violations': []
        }
        
        for rect in layout:
            for fixed_zone in self.fixed_zones:
                if self.geometry.rectangles_overlap(rect, fixed_zone):
                    result['is_valid'] = False
                    
                    overlap_area = self.geometry.calculate_overlap_area(rect, fixed_zone)
                    zone_name = fixed_zone.get('name', f"고정구역_{fixed_zone.get('id', 'unknown')}")
                    
                    violation_msg = f"'{rect['id']}'가 {zone_name}을 침범 (면적: {overlap_area:.0f}mm²)"
                    result['violations'].append(violation_msg)
                    result['zone_violations'].append({
                        'process_id': rect['id'],
                        'zone_id': fixed_zone.get('id'),
                        'zone_name': zone_name,
                        'overlap_area': overlap_area
                    })
        
        return result
    
    def check_hazard_distances(self, layout: List[Dict[str, Any]]) -> Dict[str, Any]:
        """유해인자 기반 최소 거리 검사"""
        
        result = {
            'is_valid': True,
            'violations': [],
            'distance_violations': []
        }
        
        for i, rect1 in enumerate(layout):
            id1 = rect1['id']
            hazards1 = self.hazard_factors.get(id1, [])
            
            for rect2 in layout[i + 1:]:
                id2 = rect2['id']
                hazards2 = self.hazard_factors.get(id2, [])
                
                if hazards1 and hazards2:
                    # 모든 유해인자 조합 확인
                    for hazard1 in hazards1:
                        for hazard2 in hazards2:
                            required_distance = self._get_required_hazard_distance(hazard1, hazard2)
                            
                            if required_distance > 0:
                                actual_distance = self.geometry.calculate_edge_distance(rect1, rect2)
                                
                                if actual_distance < required_distance:
                                    result['is_valid'] = False
                                    
                                    violation_msg = (f"'{id1}' ({hazard1})와 '{id2}' ({hazard2}) 간 "
                                                   f"거리 부족: {actual_distance:.0f}mm < {required_distance}mm")
                                    result['violations'].append(violation_msg)
                                    result['distance_violations'].append({
                                        'process1_id': id1,
                                        'process2_id': id2,
                                        'hazard1': hazard1,
                                        'hazard2': hazard2,
                                        'required_distance': required_distance,
                                        'actual_distance': actual_distance,
                                        'shortage': required_distance - actual_distance
                                    })
        
        return result
    
    def check_main_process_sequence(self, layout: List[Dict[str, Any]]) -> Dict[str, Any]:
        """주공정 순서 준수 검사"""
        
        result = {
            'is_valid': True,
            'violations': [],
            'warnings': [],
            'sequence_info': {}
        }
        
        # 주공정만 추출
        main_processes = [
            rect for rect in layout 
            if rect.get('building_type') == 'main' and 'main_process_sequence' in rect
        ]
        
        if not main_processes:
            result['warnings'].append("주공정이 없습니다")
            return result
        
        # 순서대로 정렬
        main_processes.sort(key=lambda x: x['main_process_sequence'])
        
        # 순서 연속성 검사
        expected_sequence = list(range(1, len(main_processes) + 1))
        actual_sequence = [p['main_process_sequence'] for p in main_processes]
        
        if actual_sequence != expected_sequence:
            result['is_valid'] = False
            result['violations'].append(
                f"주공정 순서가 연속적이지 않음: {actual_sequence} (예상: {expected_sequence})"
            )
        
        # 중복 순서 번호 검사
        sequence_counts = {}
        for process in main_processes:
            seq = process['main_process_sequence']
            sequence_counts[seq] = sequence_counts.get(seq, 0) + 1
        
        duplicates = [seq for seq, count in sequence_counts.items() if count > 1]
        if duplicates:
            result['is_valid'] = False
            result['violations'].append(f"중복된 순서 번호: {duplicates}")
        
        result['sequence_info'] = {
            'process_count': len(main_processes),
            'sequence_range': (min(actual_sequence), max(actual_sequence)) if actual_sequence else (0, 0),
            'is_consecutive': actual_sequence == expected_sequence,
            'has_duplicates': bool(duplicates)
        }
        
        return result
    
    def _get_required_hazard_distance(self, hazard1: str, hazard2: str) -> float:
        """두 유해인자 간 필요한 최소 거리 반환"""
        
        # 양방향으로 확인
        combo1 = (hazard1, hazard2)
        combo2 = (hazard2, hazard1)
        
        return (self.hazard_distance_requirements.get(combo1) or 
                self.hazard_distance_requirements.get(combo2) or 0)
    
    def get_constraint_summary(self, layout: List[Dict[str, Any]]) -> Dict[str, Any]:
        """제약 조건 검사 요약 정보 반환"""
        
        validation = self.validate_layout(layout)
        
        summary = {
            'overall_valid': validation['is_valid'],
            'total_violations': len(validation['violations']),
            'total_warnings': len(validation['warnings']),
            'constraint_status': {},
            'critical_issues': [],
            'improvement_suggestions': []
        }
        
        # 제약 조건별 상태
        for constraint_name, check_result in validation['constraints'].items():
            summary['constraint_status'][constraint_name] = {
                'passed': check_result['is_valid'],
                'violation_count': len(check_result['violations'])
            }
            
            # 심각한 문제 식별
            if not check_result['is_valid']:
                if constraint_name in ['overlaps', 'boundaries', 'fixed_zones']:
                    summary['critical_issues'].extend(check_result['violations'])
        
        # 개선 제안 생성
        suggestions = self._generate_constraint_suggestions(validation)
        summary['improvement_suggestions'] = suggestions
        
        return summary
    
    def _generate_constraint_suggestions(self, validation: Dict[str, Any]) -> List[str]:
        """제약 조건 위반에 따른 개선 제안 생성"""
        
        suggestions = []
        
        for constraint_name, check_result in validation['constraints'].items():
            if not check_result['is_valid']:
                if constraint_name == 'overlaps':
                    suggestions.append("겹치는 공정들을 분리하여 재배치하세요")
                    if 'overlapping_pairs' in check_result:
                        pairs = check_result['overlapping_pairs']
                        suggestions.append(f"특히 다음 공정들의 위치를 조정하세요: {', '.join([f'{p[0]}-{p[1]}' for p in pairs[:3]])}")
                
                elif constraint_name == 'boundaries':
                    suggestions.append("부지 경계를 벗어난 공정들을 내부로 이동하세요")
                    if 'boundary_violations' in check_result:
                        violated_ids = [v['process_id'] for v in check_result['boundary_violations']]
                        suggestions.append(f"경계 위반 공정: {', '.join(violated_ids[:5])}")
                
                elif constraint_name == 'fixed_zones':
                    suggestions.append("고정 구역(도로, 주차장 등)을 침범하지 않도록 재배치하세요")
                
                elif constraint_name == 'hazard_distances':
                    suggestions.append("유해인자가 있는 공정들 간의 안전 거리를 확보하세요")
                    if 'distance_violations' in check_result:
                        critical_violations = [v for v in check_result['distance_violations'] if v['shortage'] > 100]
                        if critical_violations:
                            suggestions.append(f"특히 위험한 조합: {len(critical_violations)}개")
                
                elif constraint_name == 'sequence':
                    suggestions.append("주공정의 순서 번호를 올바르게 설정하세요")
        
        return suggestions
    
    def check_accessibility(self, layout: List[Dict[str, Any]]) -> Dict[str, Any]:
        """접근성 검사 (도로나 출입구와의 거리)"""
        
        result = {
            'is_valid': True,
            'warnings': [],
            'accessibility_info': []
        }
        
        # 도로나 출입구 역할을 하는 고정 구역 찾기
        access_zones = [
            zone for zone in self.fixed_zones 
            if any(keyword in zone.get('name', '').lower() for keyword in ['도로', 'road', '출입', 'entrance', '게이트', 'gate'])
        ]
        
        if not access_zones:
            result['warnings'].append("접근 가능한 도로나 출입구가 정의되지 않았습니다")
            return result
        
        # 각 공정의 접근성 검사
        for rect in layout:
            min_access_distance = float('inf')
            nearest_access = None
            
            for access_zone in access_zones:
                distance = self.geometry.calculate_edge_distance(rect, access_zone)
                if distance < min_access_distance:
                    min_access_distance = distance
                    nearest_access = access_zone.get('name', access_zone.get('id'))
            
            # 접근성 정보 기록
            accessibility_info = {
                'process_id': rect['id'],
                'nearest_access': nearest_access,
                'distance': min_access_distance
            }
            result['accessibility_info'].append(accessibility_info)
            
            # 접근성 경고 (10m 이상 떨어져 있으면)
            if min_access_distance > 10.0:
                result['warnings'].append(
                    f"'{rect['id']}'의 접근성이 불량함 (가장 가까운 접근로까지 {min_access_distance:.1f}m)"
                )
        
        return result
    
    def check_minimum_spacing(self, layout: List[Dict[str, Any]], min_spacing: float = 0.5) -> Dict[str, Any]:
        """공정 간 최소 간격 검사 (m 단위)"""
        
        result = {
            'is_valid': True,
            'violations': [],
            'spacing_violations': []
        }
        
        for i, rect1 in enumerate(layout):
            for rect2 in layout[i + 1:]:
                # 겹치지 않는 경우만 간격 검사
                if not self.geometry.rectangles_overlap(rect1, rect2):
                    distance = self.geometry.calculate_edge_distance(rect1, rect2)
                    
                    if distance < min_spacing:
                        result['is_valid'] = False
                        
                        violation_msg = f"'{rect1['id']}'와 '{rect2['id']}' 간격 부족: {distance:.1f}mm < {min_spacing}mm"
                        result['violations'].append(violation_msg)
                        result['spacing_violations'].append({
                            'process1_id': rect1['id'],
                            'process2_id': rect2['id'],
                            'actual_spacing': distance,
                            'required_spacing': min_spacing,
                            'shortage': min_spacing - distance
                        })
        
        return result
    
    def suggest_constraint_fixes(self, layout: List[Dict[str, Any]]) -> Dict[str, Any]:
        """제약 조건 위반 해결 방안 제안"""
        
        validation = self.validate_layout(layout)
        fixes = {
            'overlap_fixes': [],
            'boundary_fixes': [],
            'hazard_fixes': [],
            'general_suggestions': []
        }
        
        # 겹침 해결 방안
        if not validation['constraints']['overlaps']['is_valid']:
            overlapping_pairs = validation['constraints']['overlaps'].get('overlapping_pairs', [])
            for process1_id, process2_id, overlap_area in overlapping_pairs:
                fixes['overlap_fixes'].append({
                    'processes': [process1_id, process2_id],
                    'suggested_action': f"{process1_id} 또는 {process2_id}를 최소 {overlap_area**0.5:.0f}mm 이동",
                    'overlap_area': overlap_area
                })
        
        # 경계 위반 해결 방안
        if not validation['constraints']['boundaries']['is_valid']:
            boundary_violations = validation['constraints']['boundaries'].get('boundary_violations', [])
            for violation in boundary_violations:
                process_id = violation['process_id']
                fixes['boundary_fixes'].append({
                    'process': process_id,
                    'suggested_action': f"{process_id}를 부지 내부로 이동",
                    'violations': violation['violations']
                })
        
        # 유해인자 거리 해결 방안
        if not validation['constraints']['hazard_distances']['is_valid']:
            distance_violations = validation['constraints']['hazard_distances'].get('distance_violations', [])
            for violation in distance_violations:
                fixes['hazard_fixes'].append({
                    'processes': [violation['process1_id'], violation['process2_id']],
                    'hazards': [violation['hazard1'], violation['hazard2']],
                    'suggested_action': f"{violation['shortage']:.0f}mm 추가 거리 확보 필요",
                    'required_distance': violation['required_distance']
                })
        
        # 일반적인 제안
        fixes['general_suggestions'] = [
            "전체 배치를 부지 중앙으로 이동하여 경계 여유 확보",
            "공정 크기를 줄이거나 회전하여 공간 효율성 개선",
            "고정 구역을 피해 공정들을 재그룹화",
            "유해인자가 있는 공정들을 부지 가장자리로 분산 배치"
        ]
        
        return fixes
    
    def print_constraint_report(self, layout: List[Dict[str, Any]]):
        """제약 조건 검사 리포트 출력"""
        
        validation = self.validate_layout(layout)
        
        print(f"\n🛡️  제약 조건 검사 리포트")
        print(f"=" * 50)
        
        if validation['is_valid']:
            print(f"✅ 모든 제약 조건 만족")
        else:
            print(f"❌ 제약 조건 위반 발견: {len(validation['violations'])}건")
        
        # 제약 조건별 상태
        print(f"\n📋 제약 조건별 검사 결과:")
        constraint_names = {
            'overlaps': '공정 간 겹침 없음',
            'boundaries': '부지 경계 내 배치',
            'fixed_zones': '고정 구역 비침범',
            'hazard_distances': '유해인자 안전거리',
            'sequence': '주공정 순서 준수'
        }
        
        for constraint_key, constraint_name in constraint_names.items():
            check_result = validation['constraints'][constraint_key]
            status = "✅" if check_result['is_valid'] else "❌"
            violation_count = len(check_result['violations'])
            print(f"   {status} {constraint_name}: {violation_count}건 위반")
        
        # 위반사항 상세
        if validation['violations']:
            print(f"\n❌ 위반사항 상세:")
            for i, violation in enumerate(validation['violations'][:10], 1):  # 최대 10개만 표시
                print(f"   {i}. {violation}")
            
            if len(validation['violations']) > 10:
                print(f"   ... 및 {len(validation['violations']) - 10}건 더")
        
        # 경고사항
        if validation['warnings']:
            print(f"\n⚠️  경고사항:")
            for warning in validation['warnings']:
                print(f"   - {warning}")
        
        # 통계 정보
        stats = validation['statistics']
        print(f"\n📊 배치 통계:")
        print(f"   공정 수: {stats['process_count']}개 (주공정: {stats['main_processes']}개, 부공정: {stats['sub_processes']}개)")
        print(f"   총 면적: {stats['total_area']:,.0f}mm²")
        print(f"   활용률: {stats['utilization_ratio']:.1%}")
        
        # 개선 제안
        summary = self.get_constraint_summary(layout)
        if summary['improvement_suggestions']:
            print(f"\n💡 개선 제안:")
            for suggestion in summary['improvement_suggestions']:
                print(f"   - {suggestion}")


if __name__ == "__main__":
    # 테스트 실행
    print("🧪 ConstraintHandler 테스트")
    
    # 테스트 데이터 준비
    site_width, site_height = 1000, 800
    
    fixed_zones = [
        {'id': 'road', 'x': 0, 'y': 750, 'width': 1000, 'height': 50, 'name': '도로'},
        {'id': 'parking', 'x': 10, 'y': 10, 'width': 200, 'height': 100, 'name': '주차장'}
    ]
    
    hazard_factors = {
        'process_a': ['화재', '폭발'],
        'process_b': ['독성'],
        'warehouse': ['화재']
    }
    
    # 제약 조건 처리기 초기화
    handler = ConstraintHandler(
        site_width=site_width,
        site_height=site_height,
        fixed_zones=fixed_zones,
        hazard_factors=hazard_factors
    )
    
    # 테스트 배치 (일부러 위반사항 포함)
    test_layout = [
        {'id': 'process_a', 'x': 50, 'y': 50, 'width': 150, 'height': 100, 'building_type': 'main', 'main_process_sequence': 1},
        {'id': 'process_b', 'x': 100, 'y': 80, 'width': 200, 'height': 120, 'building_type': 'main', 'main_process_sequence': 2},  # 겹침
        {'id': 'warehouse', 'x': 900, 'y': 700, 'width': 200, 'height': 150, 'building_type': 'sub'},  # 경계 위반
        {'id': 'office', 'x': 50, 'y': 50, 'width': 80, 'height': 60, 'building_type': 'sub'}  # parking과 겹침
    ]
    
    # 제약 조건 검사
    print(f"\n🔍 제약 조건 검사 실행")
    is_valid = handler.is_valid(test_layout)
    print(f"전체 유효성: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    # 상세 검사 리포트
    handler.print_constraint_report(test_layout)
    
    # 해결 방안 제안
    fixes = handler.suggest_constraint_fixes(test_layout)
    print(f"\n🔧 해결 방안 제안:")
    
    if fixes['overlap_fixes']:
        print("   겹침 해결:")
        for fix in fixes['overlap_fixes']:
            print(f"     - {fix['suggested_action']}")
    
    if fixes['boundary_fixes']:
        print("   경계 위반 해결:")
        for fix in fixes['boundary_fixes']:
            print(f"     - {fix['suggested_action']}")
    
    print("\n✅ 테스트 완료")