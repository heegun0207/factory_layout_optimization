"""
공정 분류기 모듈
주공정과 부공정을 분류하고 main_process_sequence 순서를 검증합니다.
"""

from typing import Dict, List, Any, Tuple


class ProcessClassifier:
    """공정 분류 및 순서 검증 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        초기화
        
        Args:
            config: 로드된 설정 딕셔너리
        """
        self.config = config
        self.spaces = config['spaces']
        self.main_processes = []
        self.sub_processes = []
    
    def classify_processes(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        공정을 주공정과 부공정으로 분류
        
        Returns:
            (주공정 목록, 부공정 목록) 튜플
        
        Raises:
            ValueError: 공정 분류 또는 순서에 문제가 있는 경우
        """
        print("🔍 공정 분류 시작...")
        
        main_processes_raw = {}
        sub_processes = []
        
        # 공정 타입별로 분류
        for space_id, space_info in self.spaces.items():
            building_type = space_info.get('building_type')
            
            if building_type == 'main':
                # 주공정 처리
                sequence = space_info.get('main_process_sequence')
                if sequence is None:
                    raise ValueError(f"Main process '{space_id}'에 main_process_sequence가 없습니다")
                
                process_info = space_info.copy()
                process_info['id'] = space_id
                main_processes_raw[sequence] = process_info
                
            elif building_type == 'sub':
                # 부공정 처리
                process_info = space_info.copy()
                process_info['id'] = space_id
                sub_processes.append(process_info)
            
            elif building_type == 'fixed':
                # 고정 구역은 분류하지 않음 (별도 처리)
                pass
            
            else:
                raise ValueError(f"지원되지 않는 building_type: '{building_type}' in space '{space_id}'")
        
        # 주공정이 없으면 오류
        if not main_processes_raw:
            raise ValueError("최소 1개의 main process가 필요합니다")
        
        # 주공정을 순서대로 정렬
        main_processes = self._sort_main_processes(main_processes_raw)
        
        # 검증
        self._validate_process_sequences(main_processes)
        self._validate_process_dimensions(main_processes + sub_processes)
        
        self.main_processes = main_processes
        self.sub_processes = sub_processes
        
        print(f"✅ 공정 분류 완료: 주공정 {len(main_processes)}개, 부공정 {len(sub_processes)}개")
        
        return main_processes, sub_processes
    
    def _sort_main_processes(self, main_processes_raw: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """주공정을 순서대로 정렬"""
        
        sequences = sorted(main_processes_raw.keys())
        sorted_processes = [main_processes_raw[seq] for seq in sequences]
        
        print(f"📋 주공정 순서:")
        for i, process in enumerate(sorted_processes, 1):
            sequence = process['main_process_sequence']
            print(f"   {i}. {process['id']} (순서: {sequence}) - {process.get('name', process['id'])}")
        
        return sorted_processes
    
    def _validate_process_sequences(self, main_processes: List[Dict[str, Any]]):
        """주공정 순서 유효성 검증"""
        
        sequences = [process['main_process_sequence'] for process in main_processes]
        expected_sequences = list(range(1, len(main_processes) + 1))
        
        if sequences != expected_sequences:
            raise ValueError(
                f"main_process_sequence가 연속적이지 않습니다. "
                f"현재: {sequences}, 예상: {expected_sequences}"
            )
        
        # 중복 ID 검사
        process_ids = [process['id'] for process in main_processes]
        if len(set(process_ids)) != len(process_ids):
            duplicates = [pid for pid in process_ids if process_ids.count(pid) > 1]
            raise ValueError(f"중복된 공정 ID가 있습니다: {duplicates}")
        
        print("✅ 주공정 순서 검증 완료")
    
    def _validate_process_dimensions(self, all_processes: List[Dict[str, Any]]):
        """모든 공정의 크기 유효성 검증"""
        
        site_width = self.config['site_dimensions']['width']
        site_height = self.config['site_dimensions']['height']
        
        for process in all_processes:
            width = process.get('width', 0)
            height = process.get('height', 0)
            process_id = process['id']
            
            # 크기 양수 검증
            if width <= 0 or height <= 0:
                raise ValueError(f"공정 '{process_id}'의 크기는 양수여야 합니다: {width}×{height}")
            
            # 부지 크기 초과 검증
            if width > site_width or height > site_height:
                raise ValueError(
                    f"공정 '{process_id}'가 부지 크기를 초과합니다: "
                    f"공정({width}×{height}) > 부지({site_width}×{site_height})"
                )
        
        print("✅ 공정 크기 검증 완료")
    
    def get_main_process_flow(self) -> List[str]:
        """주공정의 플로우(순서) 반환"""
        if not self.main_processes:
            return []
        
        return [process['id'] for process in self.main_processes]
    
    def get_process_by_id(self, process_id: str) -> Dict[str, Any]:
        """ID로 공정 정보 조회"""
        
        # 주공정에서 검색
        for process in self.main_processes:
            if process['id'] == process_id:
                return process
        
        # 부공정에서 검색
        for process in self.sub_processes:
            if process['id'] == process_id:
                return process
        
        raise ValueError(f"공정 '{process_id}'를 찾을 수 없습니다")
    
    def is_main_process(self, process_id: str) -> bool:
        """주공정 여부 확인"""
        return any(process['id'] == process_id for process in self.main_processes)
    
    def is_sub_process(self, process_id: str) -> bool:
        """부공정 여부 확인"""
        return any(process['id'] == process_id for process in self.sub_processes)
    
    def get_main_process_adjacency(self) -> List[Tuple[str, str]]:
        """주공정 간 인접 관계 반환 (순서대로)"""
        adjacency_pairs = []
        
        for i in range(len(self.main_processes) - 1):
            current_id = self.main_processes[i]['id']
            next_id = self.main_processes[i + 1]['id']
            adjacency_pairs.append((current_id, next_id))
        
        return adjacency_pairs
    
    def calculate_total_area(self) -> Dict[str, float]:
        """공정별 총 면적 계산"""
        
        areas = {
            'main_total': 0,
            'sub_total': 0,
            'all_total': 0,
            'site_total': self.config['site_dimensions']['width'] * self.config['site_dimensions']['height']
        }
        
        # 주공정 면적
        for process in self.main_processes:
            area = process['width'] * process['height']
            areas['main_total'] += area
            areas['all_total'] += area
        
        # 부공정 면적
        for process in self.sub_processes:
            area = process['width'] * process['height']
            areas['sub_total'] += area
            areas['all_total'] += area
        
        # 면적 비율 계산
        areas['utilization_ratio'] = areas['all_total'] / areas['site_total'] * 100
        
        return areas
    
    def get_process_statistics(self) -> Dict[str, Any]:
        """공정 통계 정보 반환"""
        
        areas = self.calculate_total_area()
        
        statistics = {
            'process_counts': {
                'main': len(self.main_processes),
                'sub': len(self.sub_processes),
                'total': len(self.main_processes) + len(self.sub_processes)
            },
            'areas': areas,
            'main_process_flow': self.get_main_process_flow(),
            'main_adjacency': self.get_main_process_adjacency()
        }
        
        # 크기별 통계
        all_processes = self.main_processes + self.sub_processes
        widths = [p['width'] for p in all_processes]
        heights = [p['height'] for p in all_processes]
        
        statistics['size_stats'] = {
            'width_range': (min(widths), max(widths)),
            'height_range': (min(heights), max(heights)),
            'avg_width': sum(widths) / len(widths),
            'avg_height': sum(heights) / len(heights)
        }
        
        return statistics
    
    def print_classification_summary(self):
        """분류 결과 요약 출력"""
        if not self.main_processes and not self.sub_processes:
            print("❌ 공정이 분류되지 않았습니다. classify_processes()를 먼저 실행하세요.")
            return
        
        stats = self.get_process_statistics()
        
        print("\n📊 공정 분류 요약:")
        print(f"   🏭 주공정: {stats['process_counts']['main']}개")
        print(f"   🔧 부공정: {stats['process_counts']['sub']}개")
        print(f"   📏 총 면적: {stats['areas']['all_total']:,.0f}mm² ({stats['areas']['utilization_ratio']:.1f}%)")
        
        print(f"\n🔄 주공정 플로우: {' → '.join(stats['main_process_flow'])}")
        
        print(f"\n📐 크기 통계:")
        print(f"   폭: {stats['size_stats']['width_range'][0]}~{stats['size_stats']['width_range'][1]}mm (평균: {stats['size_stats']['avg_width']:.0f}mm)")
        print(f"   높이: {stats['size_stats']['height_range'][0]}~{stats['size_stats']['height_range'][1]}mm (평균: {stats['size_stats']['avg_height']:.0f}mm)")


if __name__ == "__main__":
    # 테스트 실행
    print("🧪 ProcessClassifier 테스트")
    
    # 샘플 설정으로 테스트
    from config_loader import ConfigLoader, create_sample_config
    
    try:
        # 샘플 설정 생성 및 로드
        create_sample_config('test_config.json')
        loader = ConfigLoader('test_config.json')
        config = loader.load_config()
        
        # 공정 분류 테스트
        classifier = ProcessClassifier(config)
        main_processes, sub_processes = classifier.classify_processes()
        
        # 결과 출력
        classifier.print_classification_summary()
        
        # 추가 테스트
        print(f"\n🔍 추가 테스트:")
        print(f"   process_a는 주공정인가? {classifier.is_main_process('process_a')}")
        print(f"   warehouse는 부공정인가? {classifier.is_sub_process('warehouse')}")
        
        # 인접 관계 테스트
        adjacency = classifier.get_main_process_adjacency()
        print(f"   주공정 인접 관계: {adjacency}")
        
        print("\n✅ 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()