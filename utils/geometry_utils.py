"""
기하학적 유틸리티 모듈
사각형 겹침 검사, 거리 계산 등 배치 최적화에 필요한 기하학적 계산을 제공합니다.
"""

import math
from typing import Dict, List, Any, Tuple, Optional


class GeometryUtils:
    """기하학적 계산 유틸리티 클래스"""
    
    @staticmethod
    def rectangles_overlap(rect1: Dict[str, Any], rect2: Dict[str, Any]) -> bool:
        """
        두 사각형이 겹치는지 확인
        
        Args:
            rect1: 첫 번째 사각형 {'x': int, 'y': int, 'width': int, 'height': int}
            rect2: 두 번째 사각형
        
        Returns:
            겹침 여부
        """
        # 사각형 경계 계산
        r1_left = rect1['x']
        r1_right = rect1['x'] + rect1['width']
        r1_top = rect1['y']
        r1_bottom = rect1['y'] + rect1['height']
        
        r2_left = rect2['x']
        r2_right = rect2['x'] + rect2['width']
        r2_top = rect2['y']
        r2_bottom = rect2['y'] + rect2['height']
        
        # 겹침 검사 (하나라도 분리되어 있으면 겹치지 않음)
        if (r1_right <= r2_left or r2_right <= r1_left or 
            r1_bottom <= r2_top or r2_bottom <= r1_top):
            return False
        
        return True
    
    @staticmethod
    def calculate_center_distance(rect1: Dict[str, Any], rect2: Dict[str, Any]) -> float:
        """
        두 사각형의 중심점 간 거리 계산
        
        Args:
            rect1: 첫 번째 사각형
            rect2: 두 번째 사각형
        
        Returns:
            중심점 간 유클리드 거리
        """
        center1_x = rect1['x'] + rect1['width'] / 2
        center1_y = rect1['y'] + rect1['height'] / 2
        
        center2_x = rect2['x'] + rect2['width'] / 2
        center2_y = rect2['y'] + rect2['height'] / 2
        
        dx = center2_x - center1_x
        dy = center2_y - center1_y
        
        return math.sqrt(dx * dx + dy * dy)
    
    @staticmethod
    def calculate_edge_distance(rect1: Dict[str, Any], rect2: Dict[str, Any]) -> float:
        """
        두 사각형의 가장 가까운 모서리 간 거리 계산
        
        Args:
            rect1: 첫 번째 사각형
            rect2: 두 번째 사각형
        
        Returns:
            가장 가까운 모서리 간 거리 (겹치면 0)
        """
        if GeometryUtils.rectangles_overlap(rect1, rect2):
            return 0.0
        
        # 사각형 경계 계산
        r1_left = rect1['x']
        r1_right = rect1['x'] + rect1['width']
        r1_top = rect1['y']
        r1_bottom = rect1['y'] + rect1['height']
        
        r2_left = rect2['x']
        r2_right = rect2['x'] + rect2['width']
        r2_top = rect2['y']
        r2_bottom = rect2['y'] + rect2['height']
        
        # 수평 거리
        if r1_right < r2_left:
            dx = r2_left - r1_right
        elif r2_right < r1_left:
            dx = r1_left - r2_right
        else:
            dx = 0
        
        # 수직 거리
        if r1_bottom < r2_top:
            dy = r2_top - r1_bottom
        elif r2_bottom < r1_top:
            dy = r1_top - r2_bottom
        else:
            dy = 0
        
        return math.sqrt(dx * dx + dy * dy)
    
    @staticmethod
    def calculate_overlap_area(rect1: Dict[str, Any], rect2: Dict[str, Any]) -> float:
        """
        두 사각형의 겹치는 면적 계산
        
        Args:
            rect1: 첫 번째 사각형
            rect2: 두 번째 사각형
        
        Returns:
            겹치는 면적 (겹치지 않으면 0)
        """
        if not GeometryUtils.rectangles_overlap(rect1, rect2):
            return 0.0
        
        # 겹치는 영역의 경계 계산
        overlap_left = max(rect1['x'], rect2['x'])
        overlap_right = min(rect1['x'] + rect1['width'], rect2['x'] + rect2['width'])
        overlap_top = max(rect1['y'], rect2['y'])
        overlap_bottom = min(rect1['y'] + rect1['height'], rect2['y'] + rect2['height'])
        
        overlap_width = overlap_right - overlap_left
        overlap_height = overlap_bottom - overlap_top
        
        return max(0, overlap_width * overlap_height)
    
    @staticmethod
    def point_in_rectangle(point: Tuple[float, float], rect: Dict[str, Any]) -> bool:
        """
        점이 사각형 내부에 있는지 확인
        
        Args:
            point: (x, y) 좌표
            rect: 사각형
        
        Returns:
            포함 여부
        """
        px, py = point
        
        return (rect['x'] <= px <= rect['x'] + rect['width'] and 
                rect['y'] <= py <= rect['y'] + rect['height'])
    
    @staticmethod
    def rectangle_in_bounds(rect: Dict[str, Any], width: int, height: int) -> bool:
        """
        사각형이 지정된 경계 내부에 완전히 포함되는지 확인
        
        Args:
            rect: 확인할 사각형
            width: 경계 너비
            height: 경계 높이
        
        Returns:
            경계 내 포함 여부
        """
        return (rect['x'] >= 0 and rect['y'] >= 0 and 
                rect['x'] + rect['width'] <= width and 
                rect['y'] + rect['height'] <= height)
    
    @staticmethod
    def calculate_contact_length(rect1: Dict[str, Any], rect2: Dict[str, Any]) -> float:
        """
        두 사각형이 접촉하는 길이 계산
        
        Args:
            rect1: 첫 번째 사각형
            rect2: 두 번째 사각형
        
        Returns:
            접촉 길이 (접촉하지 않으면 0)
        """
        if not GeometryUtils.rectangles_overlap(rect1, rect2) and GeometryUtils.calculate_edge_distance(rect1, rect2) > 1:
            return 0.0
        
        # 수평 겹침 길이
        horizontal_overlap = max(0, min(rect1['x'] + rect1['width'], rect2['x'] + rect2['width']) - 
                                   max(rect1['x'], rect2['x']))
        
        # 수직 겹침 길이
        vertical_overlap = max(0, min(rect1['y'] + rect1['height'], rect2['y'] + rect2['height']) - 
                                 max(rect1['y'], rect2['y']))
        
        # 접촉하는 경우 겹침이 있는 방향의 길이 반환
        if horizontal_overlap > 0 and vertical_overlap > 0:
            # 실제로 겹치는 경우
            return max(horizontal_overlap, vertical_overlap)
        elif horizontal_overlap > 0:
            # 수평으로만 겹침 (위아래로 접촉)
            return horizontal_overlap
        elif vertical_overlap > 0:
            # 수직으로만 겹침 (좌우로 접촉)
            return vertical_overlap
        
        return 0.0
    
    @staticmethod
    def get_rectangle_bounds(rectangles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        사각형 목록의 전체 경계 사각형 계산
        
        Args:
            rectangles: 사각형 목록
        
        Returns:
            전체를 감싸는 경계 사각형 정보
        """
        if not rectangles:
            return {'x': 0, 'y': 0, 'width': 0, 'height': 0}
        
        min_x = min(rect['x'] for rect in rectangles)
        min_y = min(rect['y'] for rect in rectangles)
        max_x = max(rect['x'] + rect['width'] for rect in rectangles)
        max_y = max(rect['y'] + rect['height'] for rect in rectangles)
        
        return {
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        }
    
    @staticmethod
    def calculate_aspect_ratio(rect: Dict[str, Any]) -> float:
        """
        사각형의 종횡비 계산
        
        Args:
            rect: 사각형
        
        Returns:
            종횡비 (width / height)
        """
        if rect['height'] == 0:
            return float('inf')
        
        return rect['width'] / rect['height']
    
    @staticmethod
    def rotate_rectangle(rect: Dict[str, Any]) -> Dict[str, Any]:
        """
        사각형을 90도 회전 (width와 height 교체)
        
        Args:
            rect: 원본 사각형
        
        Returns:
            회전된 사각형
        """
        rotated = rect.copy()
        rotated['width'] = rect['height']
        rotated['height'] = rect['width']
        rotated['rotated'] = not rect.get('rotated', False)
        
        return rotated
    
    @staticmethod
    def translate_rectangle(rect: Dict[str, Any], dx: int, dy: int) -> Dict[str, Any]:
        """
        사각형을 이동
        
        Args:
            rect: 원본 사각형
            dx: x축 이동 거리
            dy: y축 이동 거리
        
        Returns:
            이동된 사각형
        """
        translated = rect.copy()
        translated['x'] += dx
        translated['y'] += dy
        
        return translated
    
    @staticmethod
    def find_free_space(rectangles: List[Dict[str, Any]], 
                       site_width: int, 
                       site_height: int, 
                       min_width: int, 
                       min_height: int) -> List[Dict[str, Any]]:
        """
        배치된 사각형들 사이의 빈 공간 찾기
        
        Args:
            rectangles: 배치된 사각형 목록
            site_width: 부지 너비
            site_height: 부지 높이
            min_width: 최소 필요 너비
            min_height: 최소 필요 높이
        
        Returns:
            사용 가능한 빈 공간 목록
        """
        free_spaces = []
        grid_size = min(min_width, min_height) // 2  # 그리드 크기
        
        for x in range(0, site_width - min_width + 1, grid_size):
            for y in range(0, site_height - min_height + 1, grid_size):
                # 테스트할 영역
                test_rect = {
                    'x': x,
                    'y': y,
                    'width': min_width,
                    'height': min_height
                }
                
                # 기존 사각형과 겹치는지 확인
                is_free = True
                for rect in rectangles:
                    if GeometryUtils.rectangles_overlap(test_rect, rect):
                        is_free = False
                        break
                
                if is_free:
                    free_spaces.append(test_rect)
        
        return free_spaces
    
    @staticmethod
    def calculate_utilization_ratio(rectangles: List[Dict[str, Any]], 
                                  site_width: int, 
                                  site_height: int) -> float:
        """
        부지 활용률 계산
        
        Args:
            rectangles: 배치된 사각형 목록
            site_width: 부지 너비
            site_height: 부지 높이
        
        Returns:
            활용률 (0~1)
        """
        if not rectangles:
            return 0.0
        
        total_process_area = sum(rect['width'] * rect['height'] for rect in rectangles)
        site_area = site_width * site_height
        
        return total_process_area / site_area if site_area > 0 else 0.0
    
    @staticmethod
    def calculate_compactness(rectangles: List[Dict[str, Any]]) -> float:
        """
        배치의 컴팩트성 계산 (공정들이 얼마나 집약적으로 배치되었는가)
        
        Args:
            rectangles: 배치된 사각형 목록
        
        Returns:
            컴팩트성 (0~1, 높을수록 컴팩트)
        """
        if not rectangles:
            return 0.0
        
        # 전체 공정 면적
        total_process_area = sum(rect['width'] * rect['height'] for rect in rectangles)
        
        # 최소 경계 사각형 면적
        bounds = GeometryUtils.get_rectangle_bounds(rectangles)
        bounding_area = bounds['width'] * bounds['height']
        
        return total_process_area / bounding_area if bounding_area > 0 else 0.0
    
    @staticmethod
    def find_closest_rectangles(target_rect: Dict[str, Any], 
                               rectangles: List[Dict[str, Any]], 
                               k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """
        대상 사각형에 가장 가까운 k개의 사각형 찾기
        
        Args:
            target_rect: 대상 사각형
            rectangles: 검색할 사각형 목록
            k: 반환할 개수
        
        Returns:
            (사각형, 거리) 튜플의 리스트 (거리 오름차순)
        """
        distances = []
        
        for rect in rectangles:
            if rect != target_rect:  # 자기 자신 제외
                distance = GeometryUtils.calculate_center_distance(target_rect, rect)
                distances.append((rect, distance))
        
        # 거리 순으로 정렬하고 상위 k개 반환
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    @staticmethod
    def calculate_adjacency_score(rect1: Dict[str, Any], 
                                rect2: Dict[str, Any], 
                                weight: int, 
                                preferred_gap: float = 100.0) -> float:
        """
        두 사각형 간의 인접성 점수 계산 (SLP 기반)
        
        Args:
            rect1: 첫 번째 사각형
            rect2: 두 번째 사각형
            weight: SLP 가중치 (0, 2, 4, 6, 8, 10)
            preferred_gap: 선호 거리
        
        Returns:
            인접성 점수 (높을수록 좋음)
        """
        distance = GeometryUtils.calculate_center_distance(rect1, rect2)
        
        # SLP 가중치별 점수 계산
        if weight == 10:  # A (Absolutely necessary)
            deviation = abs(distance - preferred_gap)
            return max(0, 300 - deviation * 3)
        elif weight == 8:  # E (Especially important)
            deviation = abs(distance - preferred_gap)
            return max(0, 200 - deviation * 2)
        elif weight == 6:  # I (Important)
            deviation = abs(distance - preferred_gap)
            return max(0, 150 - deviation * 1.5)
        elif weight == 4:  # O (Ordinary closeness)
            deviation = abs(distance - preferred_gap)
            return max(0, 100 - deviation)
        elif weight == 2:  # U (Unimportant)
            return 50  # 중립
        elif weight == 0:  # X (Undesirable)
            if distance < preferred_gap:
                return -(preferred_gap - distance) * 5  # 페널티
            else:
                return min(distance - preferred_gap, 100)  # 보너스
        
        return 0
    
    @staticmethod
    def generate_non_overlapping_positions(existing_rects: List[Dict[str, Any]], 
                                         new_rect_size: Tuple[int, int], 
                                         site_width: int, 
                                         site_height: int, 
                                         grid_size: int = 25) -> List[Tuple[int, int]]:
        """
        겹치지 않는 배치 위치들을 생성
        
        Args:
            existing_rects: 기존 사각형 목록
            new_rect_size: 새 사각형 크기 (width, height)
            site_width: 부지 너비
            site_height: 부지 높이
            grid_size: 그리드 크기
        
        Returns:
            유효한 위치 (x, y) 좌표 리스트
        """
        valid_positions = []
        new_width, new_height = new_rect_size
        
        for x in range(0, site_width - new_width + 1, grid_size):
            for y in range(0, site_height - new_height + 1, grid_size):
                test_rect = {
                    'x': x,
                    'y': y,
                    'width': new_width,
                    'height': new_height
                }
                
                # 기존 사각형과 겹치지 않는지 확인
                is_valid = True
                for existing_rect in existing_rects:
                    if GeometryUtils.rectangles_overlap(test_rect, existing_rect):
                        is_valid = False
                        break
                
                if is_valid:
                    valid_positions.append((x, y))
        
        return valid_positions
    
    @staticmethod
    def calculate_layout_center(rectangles: List[Dict[str, Any]]) -> Tuple[float, float]:
        """
        배치된 사각형들의 중심점 계산
        
        Args:
            rectangles: 사각형 목록
        
        Returns:
            중심점 (x, y) 좌표
        """
        if not rectangles:
            return (0.0, 0.0)
        
        bounds = GeometryUtils.get_rectangle_bounds(rectangles)
        center_x = bounds['x'] + bounds['width'] / 2
        center_y = bounds['y'] + bounds['height'] / 2
        
        return (center_x, center_y)
    
    @staticmethod
    def check_minimum_distances(rectangles: List[Dict[str, Any]], 
                              minimum_distances: Dict[str, Dict[str, float]]) -> List[str]:
        """
        최소 거리 제약 조건 위반 확인
        
        Args:
            rectangles: 배치된 사각형 목록
            minimum_distances: {id1: {id2: min_distance}} 형태의 최소 거리 맵
        
        Returns:
            위반된 제약 조건 목록
        """
        violations = []
        
        for i, rect1 in enumerate(rectangles):
            id1 = rect1['id']
            
            for rect2 in rectangles[i + 1:]:
                id2 = rect2['id']
                
                # 최소 거리 요구사항 확인
                min_dist1 = minimum_distances.get(id1, {}).get(id2, 0)
                min_dist2 = minimum_distances.get(id2, {}).get(id1, 0)
                required_min_distance = max(min_dist1, min_dist2)
                
                if required_min_distance > 0:
                    actual_distance = GeometryUtils.calculate_edge_distance(rect1, rect2)
                    
                    if actual_distance < required_min_distance:
                        violations.append(
                            f"{id1}-{id2}: 거리 {actual_distance:.1f} < 최소 {required_min_distance:.1f}"
                        )
        
        return violations


class LayoutGeometry:
    """배치 특화 기하학적 연산 클래스"""
    
    def __init__(self, site_width: int, site_height: int):
        """
        초기화
        
        Args:
            site_width: 부지 너비
            site_height: 부지 높이
        """
        self.site_width = site_width
        self.site_height = site_height
        self.utils = GeometryUtils()
    
    def center_layout(self, rectangles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        배치를 부지 중앙으로 이동
        
        Args:
            rectangles: 사각형 목록
        
        Returns:
            중앙 정렬된 사각형 목록
        """
        if not rectangles:
            return rectangles
        
        bounds = self.utils.get_rectangle_bounds(rectangles)
        
        # 중앙 정렬을 위한 오프셋 계산
        offset_x = (self.site_width - bounds['width']) // 2 - bounds['x']
        offset_y = (self.site_height - bounds['height']) // 2 - bounds['y']
        
        # 모든 사각형에 오프셋 적용
        centered_rectangles = []
        for rect in rectangles:
            centered_rect = self.utils.translate_rectangle(rect, offset_x, offset_y)
            centered_rectangles.append(centered_rect)
        
        return centered_rectangles
    
    def validate_layout(self, rectangles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        배치 유효성 검증
        
        Args:
            rectangles: 검증할 사각형 목록
        
        Returns:
            검증 결과 딕셔너리
        """
        validation_result = {
            'is_valid': True,
            'violations': [],
            'warnings': [],
            'statistics': {}
        }
        
        # 부지 경계 확인
        for rect in rectangles:
            if not self.utils.rectangle_in_bounds(rect, self.site_width, self.site_height):
                validation_result['is_valid'] = False
                validation_result['violations'].append(
                    f"공정 '{rect['id']}'가 부지 경계를 벗어남"
                )
        
        # 겹침 확인
        for i, rect1 in enumerate(rectangles):
            for rect2 in rectangles[i + 1:]:
                if self.utils.rectangles_overlap(rect1, rect2):
                    validation_result['is_valid'] = False
                    validation_result['violations'].append(
                        f"공정 '{rect1['id']}'와 '{rect2['id']}'가 겹침"
                    )
        
        # 통계 계산
        validation_result['statistics'] = {
            'process_count': len(rectangles),
            'utilization_ratio': self.utils.calculate_utilization_ratio(
                rectangles, self.site_width, self.site_height
            ),
            'compactness': self.utils.calculate_compactness(rectangles),
            'layout_bounds': self.utils.get_rectangle_bounds(rectangles)
        }
        
        return validation_result
    
    def optimize_spacing(self, rectangles: List[Dict[str, Any]], 
                        target_spacing: float = 50.0) -> List[Dict[str, Any]]:
        """
        사각형 간 간격 최적화
        
        Args:
            rectangles: 사각형 목록
            target_spacing: 목표 간격
        
        Returns:
            간격이 최적화된 사각형 목록
        """
        # 현재는 기본 구현만 제공 (추후 확장 가능)
        return rectangles


if __name__ == "__main__":
    # 테스트 실행
    print("🧪 GeometryUtils 테스트")
    
    # 테스트 사각형들
    rect1 = {'x': 10, 'y': 10, 'width': 100, 'height': 80, 'id': 'A'}
    rect2 = {'x': 120, 'y': 10, 'width': 150, 'height': 80, 'id': 'B'}
    rect3 = {'x': 50, 'y': 50, 'width': 80, 'height': 60, 'id': 'C'}  # rect1과 겹침
    
    utils = GeometryUtils()
    
    # 겹침 테스트
    print(f"rect1과 rect2 겹침: {utils.rectangles_overlap(rect1, rect2)}")  # False
    print(f"rect1과 rect3 겹침: {utils.rectangles_overlap(rect1, rect3)}")  # True
    
    # 거리 계산 테스트
    center_dist = utils.calculate_center_distance(rect1, rect2)
    edge_dist = utils.calculate_edge_distance(rect1, rect2)
    print(f"rect1과 rect2 중심거리: {center_dist:.1f}")
    print(f"rect1과 rect2 모서리거리: {edge_dist:.1f}")
    
    # 경계 계산 테스트
    bounds = utils.get_rectangle_bounds([rect1, rect2])
    print(f"전체 경계: {bounds}")
    
    # 활용률 계산 테스트
    utilization = utils.calculate_utilization_ratio([rect1, rect2], 1000, 800)
    print(f"활용률: {utilization:.3f}")
    
    # 컴팩트성 계산 테스트
    compactness = utils.calculate_compactness([rect1, rect2])
    print(f"컴팩트성: {compactness:.3f}")
    
    # 인접성 점수 테스트
    adj_score = utils.calculate_adjacency_score(rect1, rect2, weight=8, preferred_gap=100.0)
    print(f"인접성 점수 (weight=8): {adj_score:.1f}")
    
    # LayoutGeometry 테스트
    print("\n🔧 LayoutGeometry 테스트")
    layout_geom = LayoutGeometry(1000, 800)
    
    # 배치 검증 테스트
    validation = layout_geom.validate_layout([rect1, rect2, rect3])
    print(f"배치 유효성: {validation['is_valid']}")
    print(f"위반사항: {validation['violations']}")
    
    # 중앙 정렬 테스트
    centered = layout_geom.center_layout([rect1, rect2])
    print(f"중앙 정렬 후 rect1 위치: ({centered[0]['x']}, {centered[0]['y']})")
    
    print("\n✅ 테스트 완료")