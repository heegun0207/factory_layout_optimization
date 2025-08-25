"""
설정 파일 로더 모듈
JSON 파일을 읽어들여서 공정 배치 최적화에 필요한 설정을 파싱하고 검증합니다.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple


class ConfigLoader:
    """설정 파일 로더"""
    
    def __init__(self, config_path: str):
        """
        초기화
        
        Args:
            config_path: JSON 설정 파일 경로
        """
        self.config_path = Path(config_path)
        self.config = None
    
    def load_config(self) -> Dict[str, Any]:
        """
        설정 파일을 로드하고 검증
        
        Returns:
            검증된 설정 딕셔너리
        
        Raises:
            FileNotFoundError: 설정 파일을 찾을 수 없음
            ValueError: 설정 파일이 유효하지 않음
        """
        print(f"📂 설정 파일 로드 중: {self.config_path}")
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파일 형식이 올바르지 않습니다: {str(e)}")
        
        # 설정 검증
        self._validate_config()
        
        # 기본값 설정
        self._apply_defaults()
        
        print("✅ 설정 파일 로드 완료")
        return self.config
    
    def _validate_config(self):
        """설정 파일 유효성 검증 (기존 프로젝트 호환)"""
        
        # 부지 크기 검증 - 여러 형식 지원
        site_dims = None
        
        # 1. 새로운 형식 (site_dimensions)
        if 'site_dimensions' in self.config:
            site_dims = self.config['site_dimensions']
            if not isinstance(site_dims, dict) or 'width' not in site_dims or 'height' not in site_dims:
                raise ValueError("site_dimensions은 width와 height를 포함해야 합니다")
        
        # 2. 기존 프로젝트 형식 (grid_width, grid_height)
        elif 'grid_width' in self.config and 'grid_height' in self.config:
            print("🔄 기존 프로젝트 설정 파일 감지 (grid_width/grid_height)")
            site_dims = {
                'width': self.config['grid_width'],  # m 단위 그대로 유지
                'height': self.config['grid_height']
            }
            # 새 형식으로 변환
            self.config['site_dimensions'] = site_dims
            print(f"   변환 완료: {site_dims['width']}×{site_dims['height']}m")
        
        # 3. 레거시 형식 (grid_size)
        elif 'grid_size' in self.config:
            print("🔄 레거시 설정 파일 감지 (grid_size)")
            grid_size = self.config['grid_size']
            site_dims = {
                'width': grid_size,  # m 단위 그대로 유지
                'height': grid_size
            }
            self.config['site_dimensions'] = site_dims
            print(f"   변환 완료: {site_dims['width']}×{site_dims['height']}m (정사각형)")
        
        else:
            raise ValueError("부지 크기 정보가 없습니다. site_dimensions, grid_width/grid_height, 또는 grid_size가 필요합니다")
        
        if site_dims['width'] <= 0 or site_dims['height'] <= 0:
            raise ValueError("부지 크기는 양수여야 합니다")
        
        # spaces 검증
        if not isinstance(self.config['spaces'], dict):
            raise ValueError("spaces는 딕셔너리 형태여야 합니다")
        
        # 각 space 검증
        for space_id, space_info in self.config['spaces'].items():
            self._validate_space(space_id, space_info)
        
        # main_process_sequence 순서 검증 (있는 경우에만)
        main_processes = {
            space_id: space_info 
            for space_id, space_info in self.config['spaces'].items()
            if space_info.get('building_type') == 'main'
        }
        
        if main_processes:
            self._validate_main_process_sequence()
        else:
            print("⚠️ 주공정(building_type='main')이 없습니다. 기존 프로젝트 데이터를 그대로 사용합니다.")
        
        print("✅ 설정 검증 완료")
    
    def _validate_space(self, space_id: str, space_info: Dict[str, Any]):
        """개별 space 정보 검증 (기존 프로젝트 호환)"""
        
        # 1. 새로운 형식 검증
        if 'building_type' in space_info:
            # 필수 키 검증
            required_keys = ['width', 'height', 'building_type']
            for key in required_keys:
                if key not in space_info:
                    raise ValueError(f"Space '{space_id}'에 필수 키 '{key}'가 없습니다")
            
            # 크기 검증
            if space_info['width'] <= 0 or space_info['height'] <= 0:
                raise ValueError(f"Space '{space_id}'의 크기는 양수여야 합니다")
            
            # building_type 검증
            valid_types = ['main', 'sub', 'fixed']
            if space_info['building_type'] not in valid_types:
                raise ValueError(f"Space '{space_id}'의 building_type은 {valid_types} 중 하나여야 합니다")
            
            # main 타입의 경우 main_process_sequence 필수
            if space_info['building_type'] == 'main':
                if 'main_process_sequence' not in space_info:
                    raise ValueError(f"Main process '{space_id}'에는 main_process_sequence가 필요합니다")
                
                sequence = space_info['main_process_sequence']
                if not isinstance(sequence, int) or sequence < 1:
                    raise ValueError(f"main_process_sequence는 1 이상의 정수여야 합니다: {space_id}")
        
        # 2. 기존 프로젝트 형식 자동 변환
        else:
            print(f"🔄 기존 프로젝트 space 감지: {space_id}")
            
            # 기존 데이터에서 필요한 정보 추출
            if 'width' not in space_info or 'height' not in space_info:
                raise ValueError(f"Space '{space_id}'에 width 또는 height 정보가 없습니다")
            
            # building_type 자동 설정 (기본값: sub)
            if 'type' in space_info:
                # 기존 type 기반으로 building_type 설정
                old_type = space_info['type'].lower()
                if old_type in ['main_building', 'production']:
                    space_info['building_type'] = 'main'
                elif old_type in ['parking', 'road', 'fixed']:
                    space_info['building_type'] = 'fixed'
                else:
                    space_info['building_type'] = 'sub'
            else:
                space_info['building_type'] = 'sub'  # 기본값
            
            print(f"   → building_type 설정: {space_info['building_type']}")
            
            # 크기 검증
            if space_info['width'] <= 0 or space_info['height'] <= 0:
                raise ValueError(f"Space '{space_id}'의 크기는 양수여야 합니다")
    
    def _validate_main_process_sequence(self):
        """주공정 순서 유효성 검증"""
        
        main_processes = {
            space_id: space_info 
            for space_id, space_info in self.config['spaces'].items()
            if space_info.get('building_type') == 'main'
        }
        
        if not main_processes:
            raise ValueError("최소 1개의 main process가 필요합니다")
        
        # 순서 번호 추출 및 정렬
        sequences = [
            space_info['main_process_sequence'] 
            for space_info in main_processes.values()
        ]
        
        sequences.sort()
        
        # 연속성 확인 (1부터 시작해서 빠짐없이)
        expected = list(range(1, len(sequences) + 1))
        if sequences != expected:
            raise ValueError(
                f"main_process_sequence는 1부터 {len(sequences)}까지 연속적이어야 합니다. "
                f"현재: {sequences}, 예상: {expected}"
            )
        
        print(f"✅ 주공정 순서 검증 완료: {len(main_processes)}개 공정")
    
    def _apply_defaults(self):
        """기본값 설정 적용"""
        
        # adjacency_weights 기본값
        if 'adjacency_weights' not in self.config:
            self.config['adjacency_weights'] = {}
        
        # fixed_zones 기본값
        if 'fixed_zones' not in self.config:
            self.config['fixed_zones'] = []
        
        # hazard_factors 기본값
        if 'hazard_factors' not in self.config:
            self.config['hazard_factors'] = {}
        
        # optimization_params 기본값
        if 'optimization_params' not in self.config:
            self.config['optimization_params'] = {
                'genetic_algorithm': {
                    'generations': 100,
                    'population_size': 50,
                    'mutation_rate': 0.1,
                    'crossover_rate': 0.8
                },
                'simulated_annealing': {
                    'initial_temperature': 1000,
                    'cooling_rate': 0.95,
                    'min_temperature': 1
                }
            }
        
        # 각 space에 기본 id 설정
        for space_id, space_info in self.config['spaces'].items():
            if 'id' not in space_info:
                space_info['id'] = space_id
    
    def get_main_processes(self) -> List[Dict[str, Any]]:
        """주공정 목록을 순서대로 반환"""
        if not self.config:
            raise ValueError("설정이 로드되지 않았습니다")
        
        main_processes = []
        
        for space_id, space_info in self.config['spaces'].items():
            if space_info.get('building_type') == 'main':
                process_info = space_info.copy()
                process_info['id'] = space_id
                main_processes.append(process_info)
        
        # main_process_sequence 순서대로 정렬
        main_processes.sort(key=lambda x: x['main_process_sequence'])
        
        return main_processes
    
    def get_sub_processes(self) -> List[Dict[str, Any]]:
        """부공정 목록 반환"""
        if not self.config:
            raise ValueError("설정이 로드되지 않았습니다")
        
        sub_processes = []
        
        for space_id, space_info in self.config['spaces'].items():
            if space_info.get('building_type') == 'sub':
                process_info = space_info.copy()
                process_info['id'] = space_id
                sub_processes.append(process_info)
        
        return sub_processes
    
    def get_fixed_zones(self) -> List[Dict[str, Any]]:
        """고정 구역 목록 반환"""
        if not self.config:
            raise ValueError("설정이 로드되지 않았습니다")
        
        fixed_zones = []
        
        # spaces에서 fixed 타입 추출
        for space_id, space_info in self.config['spaces'].items():
            if space_info.get('building_type') == 'fixed':
                zone_info = space_info.copy()
                zone_info['id'] = space_id
                fixed_zones.append(zone_info)
        
        # fixed_zones 배열에서도 추가
        if 'fixed_zones' in self.config:
            for zone in self.config['fixed_zones']:
                if 'id' not in zone:
                    zone['id'] = f"fixed_zone_{len(fixed_zones)}"
                fixed_zones.append(zone)
        
        return fixed_zones
    
    def get_adjacency_matrix(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """인접성 매트릭스 생성"""
        if not self.config:
            raise ValueError("설정이 로드되지 않았습니다")
        
        adjacency_weights = self.config.get('adjacency_weights', {})
        adjacency_matrix = {}
        
        # 모든 공정 ID 수집
        all_process_ids = list(self.config['spaces'].keys())
        
        # 매트릭스 초기화
        for id1 in all_process_ids:
            adjacency_matrix[id1] = {}
            for id2 in all_process_ids:
                if id1 != id2:
                    # 기본값: weight=2 (U - Unimportant)
                    adjacency_matrix[id1][id2] = {
                        'weight': 2,
                        'preferred_gap': 100
                    }
        
        # 설정된 가중치 적용
        for key, weight_info in adjacency_weights.items():
            if '-' in key:
                parts = key.split('-')
                if len(parts) == 2:
                    id1, id2 = parts
                    if id1 in adjacency_matrix and id2 in adjacency_matrix[id1]:
                        adjacency_matrix[id1][id2].update(weight_info)
                    if id2 in adjacency_matrix and id1 in adjacency_matrix[id2]:
                        adjacency_matrix[id2][id1].update(weight_info)
        
        return adjacency_matrix
    
    def print_config_summary(self):
        """설정 요약 정보 출력"""
        if not self.config:
            print("❌ 설정이 로드되지 않았습니다")
            return
        
        print("\n📋 설정 파일 요약:")
        print(f"   📐 부지 크기: {self.config['site_dimensions']['width']}×{self.config['site_dimensions']['height']}mm")
        
        # 공정 통계
        spaces_by_type = {}
        for space_info in self.config['spaces'].values():
            building_type = space_info['building_type']
            spaces_by_type[building_type] = spaces_by_type.get(building_type, 0) + 1
        
        for building_type, count in spaces_by_type.items():
            type_name = {'main': '주공정', 'sub': '부공정', 'fixed': '고정구역'}.get(building_type, building_type)
            print(f"   🏭 {type_name}: {count}개")
        
        print(f"   🔗 인접성 규칙: {len(self.config.get('adjacency_weights', {}))}개")
        print(f"   ⚠️  유해인자: {len(self.config.get('hazard_factors', {}))}개")


# 테스트용 샘플 설정 생성 함수
def create_sample_config(output_path='sample_layout_config.json'):
    """테스트용 샘플 설정 파일 생성"""
    
    sample_config = {
        "site_dimensions": {
            "width": 25,
            "height": 15
        },
        "spaces": {
            "process_a": {
                "width": 4,
                "height": 3,
                "building_type": "main",
                "main_process_sequence": 1,
                "name": "공정 A"
            },
            "process_b": {
                "width": 5,
                "height": 3.5,
                "building_type": "main", 
                "main_process_sequence": 2,
                "name": "공정 B"
            },
            "process_c": {
                "width": 4.5,
                "height": 2.5,
                "building_type": "main",
                "main_process_sequence": 3,
                "name": "공정 C"
            },
            "warehouse": {
                "width": 3,
                "height": 2.5,
                "building_type": "sub",
                "name": "창고"
            },
            "office": {
                "width": 2.5,
                "height": 2,
                "building_type": "sub",
                "name": "사무실"
            },
            "parking": {
                "width": 8,
                "height": 3,
                "building_type": "fixed",
                "x": 0.5,
                "y": 0.5,
                "name": "주차장"
            }
        },
        "adjacency_weights": {
            "process_a-process_b": {
                "weight": 10,
                "preferred_gap": 1.5
            },
            "process_b-process_c": {
                "weight": 8,
                "preferred_gap": 2.0
            },
            "warehouse-process_a": {
                "weight": 6,
                "preferred_gap": 2.5
            },
            "office-parking": {
                "weight": 0,
                "preferred_gap": 200
            }
        },
        "fixed_zones": [
            {
                "id": "road",
                "x": 0,
                "y": 750,
                "width": 1000,
                "height": 50,
                "name": "도로"
            }
        ],
        "hazard_factors": {
            "process_a": ["화재", "폭발"],
            "process_b": ["독성"],
            "warehouse": ["화재"]
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    print(f"📄 샘플 설정 파일 생성 완료: {output_path}")
    return sample_config


if __name__ == "__main__":
    # 테스트 실행
    print("🧪 ConfigLoader 테스트")
    
    # 샘플 설정 파일 생성
    create_sample_config()
    
    # 설정 로더 테스트
    try:
        loader = ConfigLoader('sample_layout_config.json')
        config = loader.load_config()
        
        loader.print_config_summary()
        
        print("\n📋 주공정 목록:")
        main_processes = loader.get_main_processes()
        for process in main_processes:
            print(f"   - {process['id']}: {process['name']} ({process['width']}×{process['height']})")
        
        print("\n📋 부공정 목록:")
        sub_processes = loader.get_sub_processes()
        for process in sub_processes:
            print(f"   - {process['id']}: {process['name']} ({process['width']}×{process['height']})")
        
        print("\n✅ 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")