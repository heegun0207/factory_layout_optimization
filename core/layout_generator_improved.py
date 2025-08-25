"""
개선된 순서 기반 배치 생성기 모듈
다중 시드 포인트, 조기 가지치기, 적응형 샘플링을 적용한 고성능 버전
"""

import math
import random
from typing import Dict, List, Any, Tuple, Optional
from utils.geometry_utils import GeometryUtils


class ImprovedSequenceLayoutGenerator:
    """성능 개선된 공정 순서 기반 배치 생성기"""
    
    def __init__(self, site_width: int, site_height: int, fixed_zones: List[Dict[str, Any]]):
        """
        초기화
        
        Args:
            site_width: 부지 너비 (m)
            site_height: 부지 높이 (m)
            fixed_zones: 고정 구역 목록
        """
        self.site_width = site_width
        self.site_height = site_height
        self.fixed_zones = fixed_zones
        self.geometry = GeometryUtils()
        
        # 성능 최적화 설정
        self.enable_early_pruning = True
        self.enable_adaptive_sampling = True
        self.enable_multi_seed = True
        
        # 적응형 샘플링 파라미터
        self.max_combinations_threshold = 2000  # 이 값을 초과하면 샘플링
        self.target_sample_size = 500           # 목표 샘플 수
        self.quality_sample_ratio = 0.3         # 고품질 샘플 비율
        
        # 시드 포인트 설정
        self.max_seed_positions = 5             # 각 회전 상태별 최대 시드 수
        
        # 성능 통계
        self.stats = {
            'pruned_rotations': 0,
            'pruned_directions': 0,
            'sampled_combinations': 0,
            'seed_positions_used': 0,
            'total_evaluations': 0
        }
        
        print(f"🚀 개선된 배치 생성기 초기화: {site_width}×{site_height}m")
        print(f"   🎯 조기 가지치기: {'✅' if self.enable_early_pruning else '❌'}")
        print(f"   🎲 적응형 샘플링: {'✅' if self.enable_adaptive_sampling else '❌'}")
        print(f"   📍 다중 시드 포인트: {'✅' if self.enable_multi_seed else '❌'}")
    
    def generate_main_layout_combinations(self, main_processes: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        개선된 주공정 배치 조합 생성
        
        Args:
            main_processes: 순서대로 정렬된 주공정 목록
        
        Returns:
            가능한 모든 주공정 배치 목록
        """
        print(f"🔄 개선된 주공정 배치 조합 생성 시작: {len(main_processes)}개 공정")
        
        if not main_processes:
            return []
        
        # 1. 다중 시드 포인트 생성
        seed_strategies = self._generate_seed_strategies(main_processes[0])
        print(f"   📍 시드 전략: {len(seed_strategies)}개")
        
        # 2. 나머지 공정들의 조합 생성 (조기 가지치기 적용)
        if len(main_processes) > 1:
            rotation_combinations = self._generate_pruned_rotation_combinations(main_processes[1:])
            direction_combinations = self._generate_pruned_direction_combinations(len(main_processes) - 1)
        else:
            rotation_combinations = [[]]
            direction_combinations = [[]]
        
        raw_total = len(seed_strategies) * len(rotation_combinations) * len(direction_combinations)
        print(f"   📊 원본 조합 수: {raw_total:,}개")
        
        # 3. 적응형 샘플링 적용
        combination_indices = self._adaptive_sampling(
            len(seed_strategies), len(rotation_combinations), len(direction_combinations)
        )
        
        print(f"   🎲 샘플링 후: {len(combination_indices):,}개")
        
        # 4. 배치 생성
        valid_layouts = []
        
        for seed_idx, rot_idx, dir_idx in combination_indices:
            seed_strategy = seed_strategies[seed_idx]
            rotations = rotation_combinations[rot_idx]
            directions = direction_combinations[dir_idx]
            
            layout = self._place_main_processes_with_seed(
                main_processes, seed_strategy, rotations, directions
            )
            
            if layout:
                valid_layouts.append(layout)
            
            self.stats['total_evaluations'] += 1
        
        print(f"✅ 개선된 배치 조합 생성 완료: {len(valid_layouts)}개 유효 배치")
        self._print_performance_stats()
        
        return valid_layouts
    
    def _generate_seed_strategies(self, first_process: Dict[str, Any]) -> List[Dict[str, Any]]:
        """첫 번째 공정의 다양한 시드 전략 생성"""
        
        strategies = []
        
        # 회전 없음 + 회전 모두 고려
        for rotated in [False, True]:
            seed_positions = self._generate_strategic_seed_positions(first_process, rotated)
            optimal_positions = self._select_optimal_seed_positions(
                first_process, seed_positions, rotated
            )
            
            for pos_x, pos_y in optimal_positions:
                strategies.append({
                    'x': pos_x,
                    'y': pos_y, 
                    'rotated': rotated,
                    'process': first_process
                })
        
        self.stats['seed_positions_used'] = len(strategies)
        return strategies
    
    def _generate_strategic_seed_positions(self, process: Dict[str, Any], rotated: bool) -> List[Tuple[int, int]]:
        """전략적 시드 위치들 생성"""
        
        width = process['height'] if rotated else process['width']
        height = process['width'] if rotated else process['height']
        
        # 안전 마진
        margin = 50
        
        positions = []
        
        # 1. 중앙 위치 (기존)
        center_x = self.site_width // 2 - width // 2
        center_y = self.site_height // 2 - height // 2
        positions.append((center_x, center_y))
        
        # 2. 전략적 모서리 위치 (충분한 여유 공간 확보)
        corner_positions = [
            (margin, margin),  # 좌하단
            (self.site_width - width - margin, margin),  # 우하단
            (margin, self.site_height - height - margin),  # 좌상단
            (self.site_width - width - margin, self.site_height - height - margin),  # 우상단
        ]
        positions.extend(corner_positions)
        
        # 3. 1/3, 2/3 지점 (균형잡힌 배치)
        third_positions = [
            (self.site_width // 3 - width // 2, self.site_height // 3 - height // 2),
            (self.site_width * 2 // 3 - width // 2, self.site_height // 3 - height // 2),
            (self.site_width // 3 - width // 2, self.site_height * 2 // 3 - height // 2),
            (self.site_width * 2 // 3 - width // 2, self.site_height * 2 // 3 - height // 2),
        ]
        positions.extend(third_positions)
        
        # 4. 유효성 검사
        valid_positions = []
        for x, y in positions:
            test_rect = self._create_process_rect(process, x, y, rotated)
            if self._is_valid_seed_placement(test_rect):
                valid_positions.append((x, y))
        
        return valid_positions
    
    def _select_optimal_seed_positions(self, process: Dict[str, Any], 
                                     positions: List[Tuple[int, int]], 
                                     rotated: bool) -> List[Tuple[int, int]]:
        """인접성 및 전략적 고려사항 기반 최적 시드 위치 선택"""
        
        if not positions:
            return []
        
        scored_positions = []
        
        for pos_x, pos_y in positions:
            score = 0
            test_rect = self._create_process_rect(process, pos_x, pos_y, rotated)
            
            # 1. 고정 구역과의 관계 평가
            for fixed_zone in self.fixed_zones:
                distance = self.geometry.calculate_center_distance(test_rect, fixed_zone)
                zone_name = fixed_zone.get('name', '').lower()
                zone_id = fixed_zone.get('id', '')
                
                # 주차장과의 관계 (적당한 거리 유지)
                if any(keyword in zone_name for keyword in ['parking', '주차']) or 'ES' in zone_id:
                    if 100 <= distance <= 300:  # 100-300m 적정 거리
                        score += 50
                    elif distance > 500:
                        score -= 20
                
                # 메인게이트와의 접근성
                if any(keyword in zone_name for keyword in ['gate', '게이트', 'entrance']) or 'NB' in zone_id:
                    if distance < 200:  # 200m 이내 접근성 좋음
                        score += 40
                    elif distance > 400:
                        score -= 15
                
                # 변전소나 유틸리티와의 관계
                if any(keyword in zone_name for keyword in ['utility', '변전', 'power']):
                    if 50 <= distance <= 200:  # 적당한 거리
                        score += 30
                    elif distance < 30:  # 너무 가까우면 위험
                        score -= 40
            
            # 2. 부지 활용도 고려 (중앙 집중도 vs 분산)
            center_distance = math.sqrt(
                (pos_x + test_rect['width']/2 - self.site_width/2)**2 + 
                (pos_y + test_rect['height']/2 - self.site_height/2)**2
            )
            max_distance = math.sqrt((self.site_width/2)**2 + (self.site_height/2)**2)
            center_ratio = center_distance / max_distance
            
            # 너무 중앙도 구석도 아닌 적당한 위치 선호
            if 0.3 <= center_ratio <= 0.7:
                score += 60
            elif center_ratio < 0.2:
                score += 30  # 중앙은 나쁘지 않음
            elif center_ratio > 0.8:
                score -= 30  # 너무 구석은 불리
            
            # 3. 확장 가능성 (주변 여유 공간)
            expansion_space = min(
                pos_x,  # 왼쪽 여유
                self.site_width - (pos_x + test_rect['width']),  # 오른쪽 여유
                pos_y,  # 아래쪽 여유
                self.site_height - (pos_y + test_rect['height'])  # 위쪽 여유
            )
            
            if expansion_space > 100:
                score += 40
            elif expansion_space < 30:
                score -= 20
            
            scored_positions.append((pos_x, pos_y, score))
        
        # 점수 순으로 정렬하여 상위 N개 선택
        scored_positions.sort(key=lambda x: x[2], reverse=True)
        
        max_positions = min(self.max_seed_positions, len(scored_positions))
        return [(x, y) for x, y, score in scored_positions[:max_positions]]
    
    def _generate_pruned_rotation_combinations(self, processes: List[Dict[str, Any]]) -> List[List[bool]]:
        """조기 가지치기가 적용된 회전 조합 생성"""
        
        if not self.enable_early_pruning:
            return self._generate_rotation_combinations(len(processes))
        
        all_combinations = self._generate_rotation_combinations(len(processes))
        valid_combinations = []
        
        for combination in all_combinations:
            if self._is_viable_rotation_combination(processes, combination):
                valid_combinations.append(combination)
            else:
                self.stats['pruned_rotations'] += 1
        
        pruned_count = len(all_combinations) - len(valid_combinations)
        if pruned_count > 0:
            print(f"   ✂️  회전 조합 가지치기: {pruned_count}개 제거 ({pruned_count/len(all_combinations)*100:.1f}%)")
        
        return valid_combinations if valid_combinations else all_combinations
    
    def _is_viable_rotation_combination(self, processes: List[Dict[str, Any]], rotations: List[bool]) -> bool:
        """회전 조합의 실현 가능성 검사"""
        
        # 1. 총 면적 검사
        total_area = 0
        for i, process in enumerate(processes):
            if rotations[i]:  # 회전된 경우
                area = process['height'] * process['width']
            else:
                area = process['width'] * process['height']
            total_area += area
        
        site_area = self.site_width * self.site_height
        fixed_area = sum(zone.get('width', 0) * zone.get('height', 0) for zone in self.fixed_zones)
        available_area = site_area - fixed_area
        
        # 활용률이 80%를 초과하면 배치가 어려움
        if total_area > available_area * 0.8:
            return False
        
        # 2. 개별 공정 크기 검사 (회전 고려)
        for i, process in enumerate(processes):
            width = process['height'] if rotations[i] else process['width']
            height = process['width'] if rotations[i] else process['height']
            
            # 부지보다 큰 공정은 불가능
            if width > self.site_width or height > self.site_height:
                return False
        
        # 3. 극단적 종횡비 조합 검사 (배치 어려움 예측)
        aspect_ratios = []
        for i, process in enumerate(processes):
            width = process['height'] if rotations[i] else process['width']
            height = process['width'] if rotations[i] else process['height']
            ratio = max(width, height) / min(width, height)
            aspect_ratios.append(ratio)
        
        # 너무 많은 긴 형태의 공정들은 배치가 어려움
        long_shapes = sum(1 for ratio in aspect_ratios if ratio > 3.0)
        if long_shapes > len(processes) // 2:
            return False
        
        return True
    
    def _generate_pruned_direction_combinations(self, num_connections: int) -> List[List[str]]:
        """조기 가지치기가 적용된 방향 조합 생성"""
        
        if not self.enable_early_pruning or num_connections == 0:
            return self._generate_direction_combinations(num_connections)
        
        all_combinations = self._generate_direction_combinations(num_connections)
        valid_combinations = []
        
        for combination in all_combinations:
            if self._is_viable_direction_combination(combination):
                valid_combinations.append(combination)
            else:
                self.stats['pruned_directions'] += 1
        
        pruned_count = len(all_combinations) - len(valid_combinations)
        if pruned_count > 0:
            print(f"   ✂️  방향 조합 가지치기: {pruned_count}개 제거 ({pruned_count/len(all_combinations)*100:.1f}%)")
        
        return valid_combinations if valid_combinations else all_combinations
    
    def _is_viable_direction_combination(self, directions: List[str]) -> bool:
        """방향 조합의 실현 가능성 검사"""
        
        # 1. 극단적 방향 패턴 제거
        # 연속으로 같은 방향이 너무 많으면 일직선 배치로 공간 비효율
        direction_counts = {}
        for direction in directions:
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
        
        max_consecutive = max(direction_counts.values())
        if max_consecutive > len(directions) * 0.7:  # 70% 이상이 같은 방향
            return False
        
        # 2. 지그재그 패턴 과다 검사
        # 방향이 너무 자주 바뀌면 복잡한 배치로 비효율
        direction_changes = 0
        for i in range(1, len(directions)):
            if directions[i] != directions[i-1]:
                direction_changes += 1
        
        if direction_changes > len(directions) * 0.8:  # 80% 이상 방향 변경
            return False
        
        # 3. 대칭성/균형성 고려
        # 상하좌우 방향의 균형이 너무 치우치면 배치가 어려움
        horizontal = directions.count('left') + directions.count('right')
        vertical = directions.count('top') + directions.count('bottom')
        
        if len(directions) > 2:
            ratio = max(horizontal, vertical) / (min(horizontal, vertical) + 1)
            if ratio > 4:  # 한쪽으로 너무 치우침
                return False
        
        return True
    
    def _adaptive_sampling(self, num_seeds: int, num_rotations: int, 
                          num_directions: int) -> List[Tuple[int, int, int]]:
        """적응형 샘플링으로 조합 선택"""
        
        total_combinations = num_seeds * num_rotations * num_directions
        
        # 임계값 이하면 전수 탐색
        if not self.enable_adaptive_sampling or total_combinations <= self.max_combinations_threshold:
            indices = [(i, j, k) for i in range(num_seeds) 
                      for j in range(num_rotations) 
                      for k in range(num_directions)]
            return indices
        
        # 샘플 크기 결정
        sample_size = min(self.target_sample_size, total_combinations)
        self.stats['sampled_combinations'] = sample_size
        
        print(f"   🎲 적응형 샘플링: {total_combinations:,} → {sample_size:,} ({sample_size/total_combinations*100:.1f}%)")
        
        # 1. 고품질 샘플 (전략적 선택)
        quality_samples = int(sample_size * self.quality_sample_ratio)
        strategic_indices = self._generate_strategic_samples(
            num_seeds, num_rotations, num_directions, quality_samples
        )
        
        # 2. 다양성 샘플 (랜덤)
        diversity_samples = sample_size - len(strategic_indices)
        random_indices = self._generate_random_samples(
            num_seeds, num_rotations, num_directions, diversity_samples, 
            exclude=set(strategic_indices)
        )
        
        combined_indices = strategic_indices + random_indices
        random.shuffle(combined_indices)  # 순서 섞기
        
        return combined_indices[:sample_size]
    
    def _generate_strategic_samples(self, num_seeds: int, num_rotations: int, 
                                   num_directions: int, count: int) -> List[Tuple[int, int, int]]:
        """전략적 고품질 샘플 생성"""
        
        strategic_indices = []
        
        # 1. 최고 점수 시드들과 간단한 조합
        for seed_idx in range(min(3, num_seeds)):  # 상위 3개 시드
            for rot_idx in range(min(2, num_rotations)):  # 간단한 회전 조합
                for dir_idx in range(min(2, num_directions)):  # 간단한 방향 조합
                    strategic_indices.append((seed_idx, rot_idx, dir_idx))
        
        # 2. 대표적인 패턴들
        representative_patterns = [
            (0, 0, 0),  # 첫 번째 시드, 회전없음, 첫 방향
            (0, num_rotations//2, num_directions//2),  # 첫 시드, 중간 조합
            (min(1, num_seeds-1), 0, num_directions//4),  # 두 번째 시드
        ]
        
        for pattern in representative_patterns:
            if (pattern[0] < num_seeds and pattern[1] < num_rotations and 
                pattern[2] < num_directions and pattern not in strategic_indices):
                strategic_indices.append(pattern)
        
        return strategic_indices[:count]
    
    def _generate_random_samples(self, num_seeds: int, num_rotations: int, 
                                num_directions: int, count: int, 
                                exclude: set = None) -> List[Tuple[int, int, int]]:
        """다양성 보장 랜덤 샘플 생성"""
        
        if exclude is None:
            exclude = set()
        
        random_indices = []
        attempts = 0
        max_attempts = count * 10
        
        while len(random_indices) < count and attempts < max_attempts:
            candidate = (
                random.randint(0, num_seeds - 1),
                random.randint(0, num_rotations - 1), 
                random.randint(0, num_directions - 1)
            )
            
            if candidate not in exclude and candidate not in random_indices:
                random_indices.append(candidate)
                exclude.add(candidate)
            
            attempts += 1
        
        return random_indices
    
    def _place_main_processes_with_seed(self, main_processes: List[Dict[str, Any]], 
                                       seed_strategy: Dict[str, Any], 
                                       rotations: List[bool], 
                                       directions: List[str]) -> Optional[List[Dict[str, Any]]]:
        """시드 전략을 사용한 주공정 배치"""
        
        layout = []
        
        # 1. 첫 번째 공정 배치 (시드 전략 적용)
        first_rect = self._create_process_rect(
            seed_strategy['process'],
            seed_strategy['x'],
            seed_strategy['y'], 
            seed_strategy['rotated']
        )
        
        if not self._is_valid_placement(first_rect, layout):
            return None
        
        layout.append(first_rect)
        
        # 2. 나머지 공정들 순차 배치
        for i in range(1, len(main_processes)):
            process = main_processes[i]
            reference_rect = layout[i - 1]
            direction = directions[i - 1]
            rotation = rotations[i - 1]
            
            new_rect = self._place_adjacent_process(
                process, reference_rect, direction, rotation
            )
            
            if not new_rect or not self._is_valid_placement(new_rect, layout):
                return None
            
            layout.append(new_rect)
        
        # 3. 최종 검증 및 중앙 정렬
        if self._validate_complete_layout(layout):
            return self._center_align_layout(layout)
        
        return None
    
    # 기존 메서드들 (수정 없음)
    def _generate_rotation_combinations(self, num_processes: int) -> List[List[bool]]:
        """회전 조합 생성"""
        combinations = []
        for i in range(2 ** num_processes):
            combination = []
            for j in range(num_processes):
                combination.append((i & (1 << j)) != 0)
            combinations.append(combination)
        return combinations
    
    def _generate_direction_combinations(self, num_connections: int) -> List[List[str]]:
        """방향 조합 생성"""
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
    
    def _create_process_rect(self, process: Dict[str, Any], x: int, y: int, rotated: bool) -> Dict[str, Any]:
        """공정 정보를 기반으로 사각형 생성"""
        width = process['height'] if rotated else process['width']
        height = process['width'] if rotated else process['height']
        
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
    
    def _place_adjacent_process(self, process: Dict[str, Any], reference_rect: Dict[str, Any], 
                               direction: str, rotated: bool) -> Optional[Dict[str, Any]]:
        """참조 공정에 인접하게 새 공정 배치"""
        new_width = process['height'] if rotated else process['width']
        new_height = process['width'] if rotated else process['height']
        
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
    
    def _is_valid_seed_placement(self, rect: Dict[str, Any]) -> bool:
        """시드 배치의 유효성 검사"""
        # 부지 경계 검사
        if (rect['x'] < 0 or rect['y'] < 0 or 
            rect['x'] + rect['width'] > self.site_width or 
            rect['y'] + rect['height'] > self.site_height):
            return False
        
        # 고정 구역과의 충돌 검사
        for fixed_zone in self.fixed_zones:
            if self.geometry.rectangles_overlap(rect, fixed_zone):
                return False
        
        return True
    
    def _is_valid_placement(self, new_rect: Dict[str, Any], existing_layout: List[Dict[str, Any]]) -> bool:
        """새 공정 배치의 유효성 검사"""
        # 기존 공정과의 겹침 검사
        for existing_rect in existing_layout:
            if self.geometry.rectangles_overlap(new_rect, existing_rect):
                return False
        
        # 고정구역과의 겹침 검사
        for fixed_zone in self.fixed_zones:
            if self.geometry.rectangles_overlap(new_rect, fixed_zone):
                return False
        
        return True
    
    def _validate_complete_layout(self, layout: List[Dict[str, Any]]) -> bool:
        """완성된 배치의 전체 유효성 검사"""
        if not layout:
            return False
        
        # 공정 간 겹침 최종 확인
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
    
    def place_sub_processes_optimally(self, main_layout: List[Dict[str, Any]], 
                                    sub_processes: List[Dict[str, Any]],
                                    adjacency_weights: Dict[str, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """부공정들을 인접성 가중치 기반으로 최적 배치 (기존 로직 유지)"""
        if not sub_processes:
            return main_layout
        
        complete_layout = main_layout.copy()
        adjacency_weights = adjacency_weights or {}
        
        # 인접성 가중치에 따라 부공정 정렬
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
        
        return complete_layout
    
    def _sort_sub_processes_by_adjacency(self, sub_processes: List[Dict[str, Any]], 
                                       main_layout: List[Dict[str, Any]], 
                                       adjacency_weights: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """부공정을 인접성 가중치에 따라 정렬"""
        def get_max_adjacency_weight(sub_process):
            max_weight = 0
            sub_id = sub_process['id']
            
            for main_rect in main_layout:
                main_id = main_rect['id']
                
                weight1 = adjacency_weights.get(f"{sub_id}-{main_id}", {}).get('weight', 2)
                weight2 = adjacency_weights.get(f"{main_id}-{sub_id}", {}).get('weight', 2)
                
                max_weight = max(max_weight, weight1, weight2)
            
            return max_weight
        
        return sorted(sub_processes, key=get_max_adjacency_weight, reverse=True)
    
    def _find_optimal_sub_position(self, sub_process: Dict[str, Any], 
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
    
    def _generate_candidate_positions(self, sub_process: Dict[str, Any], 
                                    existing_layout: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """부공정의 후보 위치들 생성"""
        candidates = []
        
        # 기존 공정들 주변에 배치 시도
        for existing_rect in existing_layout:
            for direction in ['bottom', 'right', 'top', 'left']:
                for rotated in [False, True]:
                    position = self._place_adjacent_process(
                        sub_process, existing_rect, direction, rotated
                    )
                    if position:
                        candidates.append(position)
        
        # 그리드 기반 배치 시도
        grid_candidates = self._generate_grid_positions(sub_process, existing_layout)
        candidates.extend(grid_candidates)
        
        return candidates
    
    def _generate_grid_positions(self, sub_process: Dict[str, Any], 
                               existing_layout: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """그리드 기반 후보 위치 생성"""
        candidates = []
        grid_size = 25  # 25m 간격
        
        for rotated in [False, True]:
            width = sub_process['height'] if rotated else sub_process['width']
            height = sub_process['width'] if rotated else sub_process['height']
            
            x_steps = int((self.site_width - width) / grid_size) + 1
            y_steps = int((self.site_height - height) / grid_size) + 1
            
            for i in range(0, x_steps, 2):  # 2칸씩 건너뛰어 성능 향상
                for j in range(0, y_steps, 2):
                    x = i * grid_size
                    y = j * grid_size
                    position = self._create_process_rect(sub_process, x, y, rotated)
                    candidates.append(position)
        
        return candidates
    
    def _calculate_sub_position_score(self, position: Dict[str, Any], 
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
            score += self.geometry.calculate_adjacency_score(
                position, existing_rect, weight, preferred_gap
            )
        
        return score
    
    def generate_layout_code(self, layout: List[Dict[str, Any]]) -> str:
        """배치 코드 생성"""
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
            
            # 연결 길이
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
        
        if abs(dx) > abs(dy):
            return 'right' if dx > 0 else 'left'
        else:
            return 'bottom' if dy > 0 else 'top'
    
    def _calculate_contact_length(self, rect1: Dict[str, Any], rect2: Dict[str, Any]) -> int:
        """두 공정 간의 접촉 길이 계산"""
        x_overlap = max(0, min(rect1['x'] + rect1['width'], rect2['x'] + rect2['width']) - 
                           max(rect1['x'], rect2['x']))
        y_overlap = max(0, min(rect1['y'] + rect1['height'], rect2['y'] + rect2['height']) - 
                           max(rect1['y'], rect2['y']))
        
        return max(x_overlap, y_overlap)
    
    def _print_performance_stats(self):
        """성능 통계 출력"""
        print(f"\n📊 성능 최적화 통계:")
        print(f"   ✂️  가지치기: 회전 {self.stats['pruned_rotations']}개, 방향 {self.stats['pruned_directions']}개")
        print(f"   🎲 샘플링: {self.stats['sampled_combinations']}개 조합 처리")
        print(f"   📍 시드 포인트: {self.stats['seed_positions_used']}개 사용")
        print(f"   🔍 총 평가: {self.stats['total_evaluations']}개")
    
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
        
        total_process_area = sum(rect['width'] * rect['height'] for rect in layout)
        
        min_x = min(rect['x'] for rect in layout)
        min_y = min(rect['y'] for rect in layout)
        max_x = max(rect['x'] + rect['width'] for rect in layout)
        max_y = max(rect['y'] + rect['height'] for rect in layout)
        
        bounding_area = (max_x - min_x) * (max_y - min_y)
        
        return total_process_area / bounding_area if bounding_area > 0 else 0.0