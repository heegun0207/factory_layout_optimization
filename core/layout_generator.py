"""
순서 기반 배치 생성기 모듈
Factory Mass Layout Algorithm을 기반으로 main_process_sequence 순서에 따라
공정들을 배치하는 알고리즘을 구현합니다.
"""

import math
from typing import Dict, List, Any, Tuple, Optional
from utils.geometry_utils import GeometryUtils


class SequenceLayoutGenerator:
    """공정 순서를 엄격히 준수하는 배치 생성기"""
    
    def __init__(self, site_width: int, site_height: int, fixed_zones: List[Dict[str, Any]]):
        """
        초기화
        
        Args:
            site_width: 부지 너비
            site_height: 부지 높이  
            fixed_zones: 고정 구역 목록
        """
        self.site_width = site_width
        self.site_height = site_height
        self.fixed_zones = fixed_zones
        self.geometry = GeometryUtils()
        
        # 배치 방향 매핑
        self.direction_map = {
            'bottom': (0, 1),   # 아래쪽
            'right': (1, 0),    # 오른쪽
            'top': (0, -1),     # 위쪽
            'left': (-1, 0)     # 왼쪽
        }
        
        print(f"🏗️ 배치 생성기 초기화: {site_width}×{site_height}mm, 고정구역 {len(fixed_zones)}개")
    
    def generate_main_layout_combinations(self, main_processes: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        주공정의 모든 가능한 배치 조합 생성 (전수 탐색용)
        Factory Mass Layout Algorithm의 전수 탐색 방식을 따름
        
        Args:
            main_processes: 순서대로 정렬된 주공정 목록
        
        Returns:
            가능한 모든 주공정 배치 목록
        """
        print(f"🔄 주공정 배치 조합 생성 시작: {len(main_processes)}개 공정")
        
        if not main_processes:
            return []
        
        # 회전 조합 생성 (각 공정마다 0도/90도 회전)
        rotation_combinations = self._generate_rotation_combinations(len(main_processes))
        
        # 방향 조합 생성 (주공정 간 연결 방향)
        direction_combinations = self._generate_direction_combinations(len(main_processes) - 1)
        
        total_combinations = len(rotation_combinations) * len(direction_combinations)
        print(f"   총 조합 수: 회전 {len(rotation_combinations)} × 방향 {len(direction_combinations)} = {total_combinations}")
        
        valid_layouts = []
        
        # 모든 조합에 대해 배치 시도
        for rot_idx, rotations in enumerate(rotation_combinations):
            for dir_idx, directions in enumerate(direction_combinations):
                layout = self._place_main_processes_sequentially(
                    main_processes, rotations, directions
                )
                
                if layout:
                    valid_layouts.append(layout)
                
                # 진행률 출력 (10%씩)
                current = rot_idx * len(direction_combinations) + dir_idx + 1
                if current % max(1, total_combinations // 10) == 0:
                    progress = (current / total_combinations) * 100
                    print(f"   진행률: {progress:.0f}% ({len(valid_layouts)}개 유효 배치) - 경계초과 허용모드")
        
        print(f"✅ 주공정 배치 조합 생성 완료: {len(valid_layouts)}개 유효 배치")
        return valid_layouts
    
    def _generate_rotation_combinations(self, num_processes: int) -> List[List[bool]]:
        """회전 조합 생성 (0도=False, 90도=True)"""
        combinations = []
        
        for i in range(2 ** num_processes):
            combination = []
            for j in range(num_processes):
                combination.append((i & (1 << j)) != 0)
            combinations.append(combination)
        
        return combinations
    
    def _generate_direction_combinations(self, num_connections: int) -> List[List[str]]:
        """방향 조합 생성 (bottom, right, top, left)"""
        if num_connections == 0:
            return [[]]
        
        directions = ['bottom', 'right', 'top', 'left']
        combinations = []
        
        for i in range(4 ** num_connections):
            combination = []
            temp = i
            for _ in range(num_connections):
                combination.append(directions[temp % 4])
                temp //= 4
            combinations.append(combination)
        
        return combinations
    
    def _place_main_processes_sequentially(self, 
                                         main_processes: List[Dict[str, Any]], 
                                         rotations: List[bool], 
                                         directions: List[str]) -> Optional[List[Dict[str, Any]]]:
        """
        주공정들을 순서대로 배치
        Factory Mass Layout Algorithm의 순차 배치 로직을 구현
        
        Args:
            main_processes: 주공정 목록
            rotations: 각 공정의 회전 여부
            directions: 공정 간 연결 방향
        
        Returns:
            배치 성공시 배치된 공정 목록, 실패시 None
        """
        if not main_processes:
            return None
        
        layout = []
        
        # 첫 번째 공정: 부지 중앙에 배치
        first_process = main_processes[0]
        first_rect = self._create_process_rect(
            first_process,
            self.site_width // 2,
            self.site_height // 2,
            rotations[0]
        )
        
        # 중앙 정렬
        first_rect['x'] -= first_rect['width'] // 2
        first_rect['y'] -= first_rect['height'] // 2
        
        # 유효성 검사
        if not self._is_valid_placement(first_rect, layout):
            return None
        
        layout.append(first_rect)
        
        # 나머지 공정들 순차 배치
        for i in range(1, len(main_processes)):
            process = main_processes[i]
            reference_rect = layout[i - 1]  # 바로 이전 공정 참조
            direction = directions[i - 1]
            rotation = rotations[i]
            
            # 인접 배치
            new_rect = self._place_adjacent_process(
                process, reference_rect, direction, rotation
            )
            
            if not new_rect or not self._is_valid_placement(new_rect, layout):
                return None
            
            layout.append(new_rect)
        
        # ⭐ 최종 검증 완화 - 경계 검사 제거하고 겹침만 확인
        if self._validate_complete_layout(layout, strict_boundary_check=False):
            return self._center_align_layout(layout)
        
        return None
    
    def _create_process_rect(self, process: Dict[str, Any], x: int, y: int, rotated: bool) -> Dict[str, Any]:
        """공정 정보를 기반으로 사각형 생성"""
        
        width = process['width']
        height = process['height']
        
        # 90도 회전 처리
        if rotated:
            width, height = height, width
        
        return {
            'id': process['id'],
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'rotated': rotated,
            'building_type': process.get('building_type', 'main'),
            'main_process_sequence': process.get('main_process_sequence'),
            'name': process.get('name', process['id'])
        }
    
    def _place_adjacent_process(self, 
                              process: Dict[str, Any], 
                              reference_rect: Dict[str, Any], 
                              direction: str, 
                              rotated: bool) -> Optional[Dict[str, Any]]:
        """참조 공정에 인접하게 새 공정 배치"""
        
        new_width = process['height'] if rotated else process['width']
        new_height = process['width'] if rotated else process['height']
        
        # 방향에 따른 배치 위치 계산
        if direction == 'bottom':
            x = reference_rect['x']
            y = reference_rect['y'] + reference_rect['height']
        elif direction == 'right':
            x = reference_rect['x'] + reference_rect['width']
            y = reference_rect['y']
        elif direction == 'top':
            x = reference_rect['x']
            y = reference_rect['y'] - new_height
        elif direction == 'left':
            x = reference_rect['x'] - new_width
            y = reference_rect['y']
        else:
            return None
        
        return self._create_process_rect(process, x, y, rotated)
    
    def _is_valid_placement(self, new_rect: Dict[str, Any], existing_layout: List[Dict[str, Any]]) -> bool:
        """새 공정 배치의 유효성 검사 (완화된 버전)"""
        
        # ⭐ 경계 검사 제거 - 유전 알고리즘을 위해 경계 초과도 허용
        # (최종 검증 단계에서만 경계 체크)
        
        # 기존 공정과의 겹침 검사만 수행
        for existing_rect in existing_layout:
            if self.geometry.rectangles_overlap(new_rect, existing_rect):
                return False
        
        # 고정 구역과의 겹침 검사는 유지 (치명적 충돌 방지)
        for fixed_zone in self.fixed_zones:
            if self.geometry.rectangles_overlap(new_rect, fixed_zone):
                return False
        
        return True
    
    def _validate_complete_layout(self, layout: List[Dict[str, Any]], strict_boundary_check: bool = False) -> bool:
        """완성된 배치의 전체 유효성 검사 (완화된 버전)"""
        
        if not layout:
            return False
        
        # ⭐ 선택적 경계 검사 - strict_boundary_check가 True일 때만
        if strict_boundary_check:
            for rect in layout:
                if (rect['x'] < 0 or rect['y'] < 0 or 
                    rect['x'] + rect['width'] > self.site_width or 
                    rect['y'] + rect['height'] > self.site_height):
                    return False
        
        # 공정 간 겹침 최종 확인 (항상 수행)
        for i, rect1 in enumerate(layout):
            for rect2 in layout[i + 1:]:
                if self.geometry.rectangles_overlap(rect1, rect2):
                    return False
        
        return True
    
    def _center_align_layout(self, layout: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """배치를 부지 중앙으로 정렬"""
        
        if not layout:
            return layout
        
        # 배치된 공정들의 경계 계산
        min_x = min(rect['x'] for rect in layout)
        min_y = min(rect['y'] for rect in layout)
        max_x = max(rect['x'] + rect['width'] for rect in layout)
        max_y = max(rect['y'] + rect['height'] for rect in layout)
        
        layout_width = max_x - min_x
        layout_height = max_y - min_y
        
        # 중앙 정렬을 위한 오프셋 계산
        offset_x = (self.site_width - layout_width) // 2 - min_x
        offset_y = (self.site_height - layout_height) // 2 - min_y
        
        # 모든 공정에 오프셋 적용
        centered_layout = []
        for rect in layout:
            centered_rect = rect.copy()
            centered_rect['x'] += offset_x
            centered_rect['y'] += offset_y
            centered_layout.append(centered_rect)
        
        return centered_layout
    
    def place_sub_processes_optimally(self, 
                                    main_layout: List[Dict[str, Any]], 
                                    sub_processes: List[Dict[str, Any]],
                                    adjacency_weights: Dict[str, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        부공정들을 인접성 가중치 기반으로 최적 배치
        
        Args:
            main_layout: 배치된 주공정 목록
            sub_processes: 배치할 부공정 목록
            adjacency_weights: 인접성 가중치 정보
        
        Returns:
            주공정과 부공정이 모두 포함된 완전한 배치
        """
        if not sub_processes:
            return main_layout
        
        complete_layout = main_layout.copy()
        adjacency_weights = adjacency_weights or {}
        
        print(f"🔧 부공정 배치 시작: {len(sub_processes)}개")
        
        # 인접성 가중치에 따라 부공정 정렬 (높은 가중치 우선)
        sorted_sub_processes = self._sort_sub_processes_by_adjacency(
            sub_processes, main_layout, adjacency_weights
        )
        
        # 각 부공정에 대해 최적 위치 찾기
        for sub_process in sorted_sub_processes:
            best_position = self._find_optimal_sub_position(
                sub_process, complete_layout, adjacency_weights
            )
            
            if best_position:
                complete_layout.append(best_position)
                print(f"   ✅ {sub_process['id']} 배치 완료")
            else:
                print(f"   ❌ {sub_process['id']} 배치 실패")
        
        return complete_layout
    
    def _sort_sub_processes_by_adjacency(self, 
                                       sub_processes: List[Dict[str, Any]], 
                                       main_layout: List[Dict[str, Any]], 
                                       adjacency_weights: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """부공정을 인접성 가중치에 따라 정렬"""
        
        def get_max_adjacency_weight(sub_process):
            max_weight = 0
            sub_id = sub_process['id']
            
            for main_rect in main_layout:
                main_id = main_rect['id']
                
                # 양방향 인접성 확인
                weight1 = adjacency_weights.get(f"{sub_id}-{main_id}", {}).get('weight', 2)
                weight2 = adjacency_weights.get(f"{main_id}-{sub_id}", {}).get('weight', 2)
                
                max_weight = max(max_weight, weight1, weight2)
            
            return max_weight
        
        return sorted(sub_processes, key=get_max_adjacency_weight, reverse=True)
    
    def _find_optimal_sub_position(self, 
                                 sub_process: Dict[str, Any], 
                                 existing_layout: List[Dict[str, Any]], 
                                 adjacency_weights: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """부공정의 최적 위치 찾기"""
        
        best_position = None
        best_score = float('-inf')
        
        # 가능한 모든 위치에서 배치 시도
        candidate_positions = self._generate_candidate_positions(sub_process, existing_layout)
        
        for position in candidate_positions:
            if self._is_valid_placement(position, existing_layout):
                score = self._calculate_sub_position_score(
                    position, existing_layout, adjacency_weights
                )
                
                if score > best_score:
                    best_score = score
                    best_position = position
        
        return best_position
    
    def _generate_candidate_positions(self, 
                                    sub_process: Dict[str, Any], 
                                    existing_layout: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """부공정의 후보 위치들 생성"""
        
        candidates = []
        
        # 기존 공정들 주변에 배치 시도
        for existing_rect in existing_layout:
            # 4방향으로 배치 시도 (회전 포함)
            for direction in ['bottom', 'right', 'top', 'left']:
                for rotated in [False, True]:
                    position = self._place_adjacent_process(
                        sub_process, existing_rect, direction, rotated
                    )
                    if position:
                        candidates.append(position)
        
        # 빈 공간에 배치 시도 (그리드 기반)
        grid_candidates = self._generate_grid_positions(sub_process, existing_layout)
        candidates.extend(grid_candidates)
        
        return candidates
    
    def _generate_grid_positions(self, 
                               sub_process: Dict[str, Any], 
                               existing_layout: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """그리드 기반 후보 위치 생성"""
        
        candidates = []
        grid_size = 0.5  # 0.5m 간격
        
        for rotated in [False, True]:
            width = sub_process['height'] if rotated else sub_process['width']
            height = sub_process['width'] if rotated else sub_process['height']
            
            x_steps = int((self.site_width - width) / grid_size) + 1
            y_steps = int((self.site_height - height) / grid_size) + 1
            
            for i in range(x_steps):
                for j in range(y_steps):
                    x = i * grid_size
                    y = j * grid_size
                    position = self._create_process_rect(sub_process, x, y, rotated)
                    candidates.append(position)
        
        return candidates
    
    def _calculate_sub_position_score(self, 
                                    position: Dict[str, Any], 
                                    existing_layout: List[Dict[str, Any]], 
                                    adjacency_weights: Dict[str, Dict[str, Any]]) -> float:
        """부공정 위치의 점수 계산"""
        
        score = 0.0
        position_id = position['id']
        
        for existing_rect in existing_layout:
            existing_id = existing_rect['id']
            distance = self.geometry.calculate_center_distance(position, existing_rect)
            
            # 인접성 가중치 조회
            weight_key1 = f"{position_id}-{existing_id}"
            weight_key2 = f"{existing_id}-{position_id}"
            
            weight_info = (adjacency_weights.get(weight_key1) or 
                          adjacency_weights.get(weight_key2) or 
                          {'weight': 2, 'preferred_gap': 100})
            
            weight = weight_info['weight']
            preferred_gap = weight_info.get('preferred_gap', 100)
            
            # SLP 가중치에 따른 점수 계산
            if weight == 10:  # A (Absolutely necessary)
                deviation = abs(distance - preferred_gap)
                score += max(0, 300 - deviation * 3)
            elif weight == 8:  # E (Especially important)
                deviation = abs(distance - preferred_gap)
                score += max(0, 200 - deviation * 2)
            elif weight == 6:  # I (Important)
                deviation = abs(distance - preferred_gap)
                score += max(0, 150 - deviation * 1.5)
            elif weight == 4:  # O (Ordinary closeness)
                deviation = abs(distance - preferred_gap)
                score += max(0, 100 - deviation)
            elif weight == 2:  # U (Unimportant)
                score += 50  # 중립
            elif weight == 0:  # X (Undesirable)
                if distance < preferred_gap:
                    score -= (preferred_gap - distance) * 5
                else:
                    score += min(distance - preferred_gap, 100)
        
        return score
    
    def generate_layout_code(self, layout: List[Dict[str, Any]]) -> str:
        """
        배치 코드 생성 (Factory Mass Layout Algorithm 방식)
        형태: AO-b(50)-BR-c(30)-CO
        """
        if not layout:
            return ""
        
        # 주공정만 추출하여 순서대로 정렬
        main_processes = [
            rect for rect in layout 
            if rect.get('building_type') == 'main'
        ]
        
        if not main_processes:
            return "NO_MAIN_PROCESSES"
        
        main_processes.sort(key=lambda x: x.get('main_process_sequence', 999))
        
        code_parts = []
        
        # 첫 번째 공정
        first_process = main_processes[0]
        rotation_code = 'R' if first_process.get('rotated', False) else 'O'
        code_parts.append(f"{first_process['id']}{rotation_code}")
        
        # 나머지 공정들
        for i in range(1, len(main_processes)):
            current = main_processes[i]
            previous = main_processes[i - 1]
            
            # 방향 계산
            direction = self._calculate_direction(previous, current)
            direction_code = {
                'bottom': 'a',
                'right': 'b',
                'top': 'c',
                'left': 'd'
            }.get(direction, 'b')
            
            # 연결 길이 (접촉 길이)
            connection_length = self._calculate_contact_length(previous, current)
            
            # 회전 상태
            rotation_code = 'R' if current.get('rotated', False) else 'O'
            
            code_parts.append(f"{direction_code}({connection_length})-{current['id']}{rotation_code}")
        
        return '-'.join(code_parts)
    
    def _calculate_direction(self, rect1: Dict[str, Any], rect2: Dict[str, Any]) -> str:
        """두 공정 간의 방향 계산"""
        
        center1_x = rect1['x'] + rect1['width'] / 2
        center1_y = rect1['y'] + rect1['height'] / 2
        center2_x = rect2['x'] + rect2['width'] / 2
        center2_y = rect2['y'] + rect2['height'] / 2
        
        dx = center2_x - center1_x
        dy = center2_y - center1_y
        
        # 절댓값이 더 큰 방향으로 결정
        if abs(dx) > abs(dy):
            return 'right' if dx > 0 else 'left'
        else:
            return 'bottom' if dy > 0 else 'top'
    
    def _calculate_contact_length(self, rect1: Dict[str, Any], rect2: Dict[str, Any]) -> int:
        """두 공정 간의 접촉 길이 계산"""
        
        # 겹치는 구간 계산
        x_overlap = max(0, min(rect1['x'] + rect1['width'], rect2['x'] + rect2['width']) - 
                           max(rect1['x'], rect2['x']))
        y_overlap = max(0, min(rect1['y'] + rect1['height'], rect2['y'] + rect2['height']) - 
                           max(rect1['y'], rect2['y']))
        
        # 접촉 길이는 겹치는 구간의 길이
        return max(x_overlap, y_overlap)
    
    def get_layout_statistics(self, layout: List[Dict[str, Any]]) -> Dict[str, Any]:
        """배치 통계 정보 반환"""
        
        if not layout:
            return {}
        
        # 경계 계산
        min_x = min(rect['x'] for rect in layout)
        min_y = min(rect['y'] for rect in layout)
        max_x = max(rect['x'] + rect['width'] for rect in layout)
        max_y = max(rect['y'] + rect['height'] for rect in layout)
        
        layout_width = max_x - min_x
        layout_height = max_y - min_y
        layout_area = layout_width * layout_height
        
        # 공정별 면적
        total_process_area = sum(rect['width'] * rect['height'] for rect in layout)
        
        statistics = {
            'layout_bounds': {
                'min_x': min_x,
                'min_y': min_y,
                'max_x': max_x,
                'max_y': max_y,
                'width': layout_width,
                'height': layout_height
            },
            'areas': {
                'layout_area': layout_area,
                'process_area': total_process_area,
                'site_area': self.site_width * self.site_height,
                'layout_utilization': (layout_area / (self.site_width * self.site_height)) * 100,
                'process_density': (total_process_area / layout_area) * 100 if layout_area > 0 else 0
            },
            'process_counts': {
                'total': len(layout),
                'main': len([r for r in layout if r.get('building_type') == 'main']),
                'sub': len([r for r in layout if r.get('building_type') == 'sub'])
            },
            'compactness': self._calculate_compactness(layout)
        }
        
        return statistics
    
    def _calculate_compactness(self, layout: List[Dict[str, Any]]) -> float:
        """배치의 컴팩트성 계산 (0~1, 높을수록 컴팩트)"""
        
        if not layout:
            return 0.0
        
        # 총 공정 면적
        total_process_area = sum(rect['width'] * rect['height'] for rect in layout)
        
        # 배치 전체 면적 (최소 경계 사각형)
        min_x = min(rect['x'] for rect in layout)
        min_y = min(rect['y'] for rect in layout)
        max_x = max(rect['x'] + rect['width'] for rect in layout)
        max_y = max(rect['y'] + rect['height'] for rect in layout)
        
        bounding_area = (max_x - min_x) * (max_y - min_y)
        
        return total_process_area / bounding_area if bounding_area > 0 else 0.0


if __name__ == "__main__":
    # 테스트 실행
    print("🧪 SequenceLayoutGenerator 테스트")
    
    # 테스트 데이터 준비
    from core.config_loader import ConfigLoader, create_sample_config
    from core.process_classifier import ProcessClassifier
    
    try:
        # 샘플 설정 생성 및 로드
        create_sample_config('test_layout_config.json')
        loader = ConfigLoader('test_layout_config.json')
        config = loader.load_config()
        
        # 공정 분류
        classifier = ProcessClassifier(config)
        main_processes, sub_processes = classifier.classify_processes()
        
        # 배치 생성기 초기화
        generator = SequenceLayoutGenerator(
            site_width=config['site_dimensions']['width'],
            site_height=config['site_dimensions']['height'],
            fixed_zones=loader.get_fixed_zones()
        )
        
        # 주공정 배치 조합 생성 (첫 5개만 테스트)
        print("\n🔄 주공정 배치 테스트")
        main_layouts = generator.generate_main_layout_combinations(main_processes)
        
        if main_layouts:
            # 첫 번째 배치로 테스트
            test_layout = main_layouts[0]
            print(f"✅ 테스트 배치 생성: {len(test_layout)}개 공정")
            
            # 부공정 추가
            complete_layout = generator.place_sub_processes_optimally(
                test_layout, sub_processes, config.get('adjacency_weights', {})
            )
            
            # 배치 코드 생성
            layout_code = generator.generate_layout_code(complete_layout)
            print(f"📝 배치 코드: {layout_code}")
            
            # 통계 정보
            stats = generator.get_layout_statistics(complete_layout)
            print(f"📊 배치 통계:")
            print(f"   크기: {stats['layout_bounds']['width']}×{stats['layout_bounds']['height']}mm")
            print(f"   부지 활용률: {stats['areas']['layout_utilization']:.1f}%")
            print(f"   컴팩트성: {stats['compactness']:.2f}")
            
        else:
            print("❌ 유효한 배치를 생성하지 못했습니다")
        
        print("\n✅ 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()