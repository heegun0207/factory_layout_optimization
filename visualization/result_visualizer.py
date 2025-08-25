"""
결과 시각화 모듈
최적화 결과를 시각화하여 표시합니다. 상위 4개는 크게, 나머지는 작게 표시합니다.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Button
import numpy as np
from typing import Dict, List, Any, Optional
import time


class ResultVisualizer:
    """최적화 결과 시각화기"""
    
    def __init__(self, site_width: int, site_height: int):
        """
        초기화
        
        Args:
            site_width: 부지 너비
            site_height: 부지 높이
        """
        self.site_width = site_width
        self.site_height = site_height
        
        # 색상 매핑
        self.process_colors = {
            'main': '#FF6B6B',      # 빨강 계열 (주공정)
            'sub': '#4ECDC4',       # 청록 계열 (부공정)
            'fixed': '#95A5A6'      # 회색 (고정구역)
        }
        
        # 현재 표시 중인 솔루션들
        self.solutions = []
        self.current_detail_index = 0
        
        print(f"📊 결과 시각화기 초기화: {site_width}×{site_height}mm")
    
    def show_results(self, solutions: List[Dict[str, Any]]):
        """
        최적화 결과 표시
        
        Args:
            solutions: 솔루션 목록 (적합도 순으로 정렬된 상태)
        """
        if not solutions:
            print("❌ 표시할 솔루션이 없습니다.")
            return
        
        self.solutions = solutions
        
        # 상위 4개와 나머지로 분리
        top_4 = solutions[:4]
        remaining = solutions[4:8] if len(solutions) > 4 else []
        
        print(f"📊 {len(solutions)}개 솔루션 시각화 시작")
        print(f"   상위 4개: 큰 화면으로 표시")
        print(f"   나머지 {len(remaining)}개: 작은 화면으로 표시")
        
        # 결과 창 생성
        self._create_result_window(top_4, remaining)
    
    def _create_result_window(self, top_4: List[Dict[str, Any]], remaining: List[Dict[str, Any]]):
        """결과 표시 창 생성"""
        
        # 창 크기 설정 (가로로 긴 형태)
        fig = plt.figure(figsize=(20, 12))
        fig.suptitle('🏆 공정 배치 최적화 결과', fontsize=20, fontweight='bold', y=0.95)
        
        # 상위 4개 솔루션 (2x2 그리드)
        for i, solution in enumerate(top_4):
            ax = plt.subplot(2, 4, i + 1)
            self._draw_layout(ax, solution, title=f"#{i+1}: {solution['fitness']:.1f}점", large=True)
        
        # 나머지 솔루션들 (세로로 작게)
        if remaining:
            for i, solution in enumerate(remaining[:4]):  # 최대 4개 더 표시
                ax = plt.subplot(2, 4, i + 5)
                self._draw_layout(ax, solution, title=f"#{i+5}: {solution['fitness']:.1f}점", large=False)
        
        # 상세 정보 표시 영역 추가
        self._add_detail_panel(fig)
        
        # 버튼 추가
        self._add_control_buttons(fig)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.90, bottom=0.05)
        plt.show()
    
    def _draw_layout(self, ax, solution: Dict[str, Any], title: str, large: bool = True):
        """개별 배치 그리기"""
        
        layout = solution['layout']
        
        # 축 설정
        ax.set_xlim(0, self.site_width)
        ax.set_ylim(0, self.site_height)
        ax.set_aspect('equal')
        ax.set_title(title, fontsize=12 if large else 10, fontweight='bold')
        
        if large:
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('X (mm)', fontsize=10)
            ax.set_ylabel('Y (mm)', fontsize=10)
        else:
            ax.grid(True, alpha=0.2)
            ax.tick_params(labelsize=8)
        
        # 부지 경계
        site_boundary = patches.Rectangle(
            (0, 0), self.site_width, self.site_height,
            linewidth=2, edgecolor='black', facecolor='none'
        )
        ax.add_patch(site_boundary)
        
        # 공정들 그리기
        for rect in layout:
            building_type = rect.get('building_type', 'sub')
            color = self.process_colors.get(building_type, '#CCCCCC')
            
            # 사각형
            rectangle = patches.Rectangle(
                (rect['x'], rect['y']), 
                rect['width'], 
                rect['height'],
                linewidth=1,
                edgecolor='black',
                facecolor=color,
                alpha=0.8
            )
            ax.add_patch(rectangle)
            
            # 라벨 (큰 화면에만)
            if large:
                center_x = rect['x'] + rect['width'] / 2
                center_y = rect['y'] + rect['height'] / 2
                
                rotation_marker = "↻" if rect.get('rotated', False) else ""
                label = f"{rect['id']}{rotation_marker}"
                
                ax.text(center_x, center_y, label, 
                       ha='center', va='center', 
                       fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.1", facecolor='white', alpha=0.9))
        
        # 메타 정보 표시 (작은 화면용)
        if not large:
            method = solution.get('method', 'unknown')
            code = solution.get('code', '')
            info_text = f"{method}\n{code[:15]}..." if len(code) > 15 else f"{method}\n{code}"
            
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
                   fontsize=7, verticalalignment='top',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    def _add_detail_panel(self, fig):
        """상세 정보 패널 추가"""
        
        # 하단에 상세 정보 텍스트 영역 생성
        detail_ax = fig.add_axes([0.05, 0.02, 0.7, 0.08])  # [left, bottom, width, height]
        detail_ax.axis('off')
        
        # 첫 번째 솔루션의 상세 정보 표시
        if self.solutions:
            self._update_detail_panel(detail_ax, self.solutions[0])
        
        self.detail_ax = detail_ax
    
    def _update_detail_panel(self, ax, solution: Dict[str, Any]):
        """상세 정보 패널 업데이트"""
        
        ax.clear()
        ax.axis('off')
        
        # 솔루션 정보 텍스트 생성
        fitness = solution.get('fitness', 0)
        method = solution.get('method', 'unknown')
        code = solution.get('code', 'N/A')
        generation = solution.get('generation', 'N/A')
        
        layout = solution['layout']
        main_count = len([r for r in layout if r.get('building_type') == 'main'])
        sub_count = len([r for r in layout if r.get('building_type') == 'sub'])
        
        # 배치 통계
        total_area = sum(r['width'] * r['height'] for r in layout)
        site_area = self.site_width * self.site_height
        utilization = (total_area / site_area) * 100
        
        detail_text = (
            f"🏆 적합도: {fitness:.2f}점  |  "
            f"🔧 알고리즘: {method}  |  "
            f"📋 배치코드: {code}  |  "
            f"🔢 세대: {generation}\n"
            f"🏭 공정수: 총 {len(layout)}개 (주공정 {main_count}개, 부공정 {sub_count}개)  |  "
            f"📊 부지활용률: {utilization:.1f}%  |  "
            f"📐 총면적: {total_area:,.0f}mm²"
        )
        
        ax.text(0, 0.5, detail_text, transform=ax.transAxes,
               fontsize=11, verticalalignment='center',
               bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.3))
    
    def _add_control_buttons(self, fig):
        """컨트롤 버튼 추가"""
        
        # 버튼 영역
        button_area = fig.add_axes([0.8, 0.02, 0.18, 0.08])
        button_area.axis('off')
        
        # 상세 보기 버튼
        detail_btn_ax = fig.add_axes([0.81, 0.06, 0.08, 0.03])
        detail_btn = Button(detail_btn_ax, '상세보기', color='lightgreen')
        detail_btn.on_clicked(self._show_detailed_view)
        
        # 비교 보기 버튼  
        compare_btn_ax = fig.add_axes([0.90, 0.06, 0.08, 0.03])
        compare_btn = Button(compare_btn_ax, '비교보기', color='lightcoral')
        compare_btn.on_clicked(self._show_comparison_view)
        
        # 저장 버튼
        save_btn_ax = fig.add_axes([0.81, 0.02, 0.08, 0.03])
        save_btn = Button(save_btn_ax, '저장', color='lightyellow')
        save_btn.on_clicked(self._save_results)
        
        # 리포트 버튼
        report_btn_ax = fig.add_axes([0.90, 0.02, 0.08, 0.03])
        report_btn = Button(report_btn_ax, '리포트', color='lightgray')
        report_btn.on_clicked(self._generate_report)
    
    def _show_detailed_view(self, event):
        """상세 보기 창 표시"""
        if not self.solutions:
            return
        
        # 새로운 창에서 첫 번째 솔루션 상세 표시
        solution = self.solutions[0]
        self._create_detailed_solution_view(solution)
    
    def _create_detailed_solution_view(self, solution: Dict[str, Any]):
        """개별 솔루션 상세 보기 창"""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'상세 분석: 적합도 {solution["fitness"]:.2f}점', fontsize=16, fontweight='bold')
        
        # 1. 메인 배치도 (좌상)
        self._draw_detailed_layout(axes[0, 0], solution)
        
        # 2. 인접성 분석 (우상)
        self._draw_adjacency_analysis(axes[0, 1], solution)
        
        # 3. 적합도 분해 (좌하)
        self._draw_fitness_breakdown(axes[1, 0], solution)
        
        # 4. 배치 통계 (우하)
        self._draw_layout_statistics(axes[1, 1], solution)
        
        plt.tight_layout()
        plt.show()
    
    def _draw_detailed_layout(self, ax, solution: Dict[str, Any]):
        """상세 배치도 그리기"""
        
        ax.set_title('배치도', fontsize=14, fontweight='bold')
        layout = solution['layout']
        
        # 기본 배치 그리기
        self._draw_layout(ax, solution, title="", large=True)
        
        # 추가 정보: 공정 번호, 크기 정보
        for rect in layout:
            center_x = rect['x'] + rect['width'] / 2
            center_y = rect['y'] + rect['height'] / 2
            
            # 크기 정보 추가
            size_text = f"{rect['width']}×{rect['height']}"
            ax.text(center_x, center_y - 15, size_text, 
                   ha='center', va='center', fontsize=8,
                   bbox=dict(boxstyle="round,pad=0.1", facecolor='yellow', alpha=0.7))
    
    def _draw_adjacency_analysis(self, ax, solution: Dict[str, Any]):
        """인접성 분석 그래프"""
        
        ax.set_title('인접성 분석', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        layout = solution['layout']
        
        # 간단한 인접성 매트릭스 시각화
        process_ids = [r['id'] for r in layout]
        n = len(process_ids)
        
        if n > 1:
            # 거리 매트릭스 계산
            distance_matrix = np.zeros((n, n))
            
            for i, rect1 in enumerate(layout):
                for j, rect2 in enumerate(layout):
                    if i != j:
                        # 중심점 간 거리
                        cx1 = rect1['x'] + rect1['width'] / 2
                        cy1 = rect1['y'] + rect1['height'] / 2
                        cx2 = rect2['x'] + rect2['width'] / 2
                        cy2 = rect2['y'] + rect2['height'] / 2
                        
                        distance = np.sqrt((cx2 - cx1)**2 + (cy2 - cy1)**2)
                        distance_matrix[i, j] = distance
            
            # 히트맵 표시
            im = ax.imshow(distance_matrix, cmap='viridis_r', aspect='auto')
            ax.set_xticks(range(n))
            ax.set_yticks(range(n))
            ax.set_xticklabels(process_ids, rotation=45)
            ax.set_yticklabels(process_ids)
            
            # 컬러바 추가
            plt.colorbar(im, ax=ax, label='거리 (mm)')
        
        else:
            ax.text(0.5, 0.5, '분석할 공정이 부족합니다', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _draw_fitness_breakdown(self, ax, solution: Dict[str, Any]):
        """적합도 분해 차트"""
        
        ax.set_title('적합도 구성 요소', fontsize=14, fontweight='bold')
        
        # 가상의 적합도 구성 요소 (실제로는 FitnessCalculator에서 가져와야 함)
        components = {
            '인접성': 250,
            '순서준수': 180,
            '활용률': 120,
            '컴팩트성': 90,
            '접근성': 80
        }
        
        # 막대 그래프
        categories = list(components.keys())
        values = list(components.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        bars = ax.bar(categories, values, color=colors, alpha=0.8)
        ax.set_ylabel('점수')
        ax.tick_params(axis='x', rotation=45)
        
        # 값 표시
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                   f'{value}', ha='center', va='bottom')
    
    def _draw_layout_statistics(self, ax, solution: Dict[str, Any]):
        """배치 통계 표시"""
        
        ax.set_title('배치 통계', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        layout = solution['layout']
        
        # 통계 계산
        total_processes = len(layout)
        main_processes = len([r for r in layout if r.get('building_type') == 'main'])
        sub_processes = len([r for r in layout if r.get('building_type') == 'sub'])
        
        total_area = sum(r['width'] * r['height'] for r in layout)
        site_area = self.site_width * self.site_height
        utilization = (total_area / site_area) * 100
        
        # 배치 범위
        min_x = min(r['x'] for r in layout) if layout else 0
        max_x = max(r['x'] + r['width'] for r in layout) if layout else 0
        min_y = min(r['y'] for r in layout) if layout else 0
        max_y = max(r['y'] + r['height'] for r in layout) if layout else 0
        
        layout_width = max_x - min_x
        layout_height = max_y - min_y
        
        # 회전된 공정 수
        rotated_count = len([r for r in layout if r.get('rotated', False)])
        
        # 통계 텍스트 생성
        stats_text = f"""
📊 배치 통계 정보

🏭 공정 구성:
   • 총 공정 수: {total_processes}개
   • 주공정: {main_processes}개
   • 부공정: {sub_processes}개
   • 회전된 공정: {rotated_count}개

📐 면적 정보:
   • 총 공정 면적: {total_area:.1f} m²
   • 부지 면적: {site_area:.1f} m²
   • 부지 활용률: {utilization:.1f}%

📏 배치 범위:
   • 배치 크기: {layout_width:.1f} × {layout_height:.1f} m
   • 배치 위치: ({min_x:.1f}, {min_y:.1f}) ~ ({max_x:.1f}, {max_y:.1f})

🎯 기타 정보:
   • 배치 코드: {solution.get('code', 'N/A')}
   • 생성 방법: {solution.get('method', 'unknown')}
   • 적합도 점수: {solution.get('fitness', 0):.2f}점
        """
        
        ax.text(0.05, 0.95, stats_text.strip(), transform=ax.transAxes,
               fontsize=10, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.3))
    
    def _show_comparison_view(self, event):
        """비교 보기 창 표시"""
        if len(self.solutions) < 2:
            print("⚠️ 비교할 솔루션이 부족합니다 (최소 2개 필요)")
            return
        
        # 상위 2개 솔루션 비교
        self._create_comparison_view(self.solutions[0], self.solutions[1])
    
    def _create_comparison_view(self, solution1: Dict[str, Any], solution2: Dict[str, Any]):
        """두 솔루션 비교 보기"""
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle('솔루션 비교 분석', fontsize=16, fontweight='bold')
        
        # 솔루션 1 배치
        axes[0, 0].set_title(f'솔루션 #1 (적합도: {solution1["fitness"]:.2f})', fontweight='bold')
        self._draw_layout(axes[0, 0], solution1, title="", large=True)
        
        # 솔루션 2 배치
        axes[0, 1].set_title(f'솔루션 #2 (적합도: {solution2["fitness"]:.2f})', fontweight='bold')
        self._draw_layout(axes[0, 1], solution2, title="", large=True)
        
        # 적합도 비교
        self._draw_fitness_comparison(axes[1, 0], solution1, solution2)
        
        # 통계 비교
        self._draw_statistics_comparison(axes[1, 1], solution1, solution2)
        
        plt.tight_layout()
        plt.show()
    
    def _draw_fitness_comparison(self, ax, solution1: Dict[str, Any], solution2: Dict[str, Any]):
        """적합도 비교 차트"""
        
        ax.set_title('적합도 구성 요소 비교', fontweight='bold')
        
        # 가상의 구성 요소 (실제로는 fitness_calculator에서 가져와야 함)
        components = ['인접성', '순서준수', '활용률', '컴팩트성', '접근성']
        
        # 임의의 값들 (실제 구현에서는 실제 분해된 점수 사용)
        values1 = [250, 180, 120, 90, 80]
        values2 = [230, 200, 110, 95, 85]
        
        x = np.arange(len(components))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, values1, width, label=f'솔루션 #1 ({solution1["fitness"]:.1f})', 
                      color='#FF6B6B', alpha=0.8)
        bars2 = ax.bar(x + width/2, values2, width, label=f'솔루션 #2 ({solution2["fitness"]:.1f})', 
                      color='#4ECDC4', alpha=0.8)
        
        ax.set_xlabel('구성 요소')
        ax.set_ylabel('점수')
        ax.set_xticks(x)
        ax.set_xticklabels(components, rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 값 표시
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                       f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    def _draw_statistics_comparison(self, ax, solution1: Dict[str, Any], solution2: Dict[str, Any]):
        """통계 비교 표"""
        
        ax.set_title('배치 통계 비교', fontweight='bold')
        ax.axis('off')
        
        # 통계 계산
        def calc_stats(solution):
            layout = solution['layout']
            total_area = sum(r['width'] * r['height'] for r in layout)
            site_area = self.site_width * self.site_height
            
            min_x = min(r['x'] for r in layout) if layout else 0
            max_x = max(r['x'] + r['width'] for r in layout) if layout else 0
            min_y = min(r['y'] for r in layout) if layout else 0
            max_y = max(r['y'] + r['height'] for r in layout) if layout else 0
            
            return {
                'processes': len(layout),
                'utilization': (total_area / site_area) * 100,
                'layout_width': max_x - min_x,
                'layout_height': max_y - min_y,
                'rotated': len([r for r in layout if r.get('rotated', False)])
            }
        
        stats1 = calc_stats(solution1)
        stats2 = calc_stats(solution2)
        
        # 비교 테이블 생성
        comparison_text = f"""
{'항목':<15} {'솔루션 #1':<12} {'솔루션 #2':<12} {'차이':<10}
{'-'*50}
{'공정 수':<15} {stats1['processes']:<12} {stats2['processes']:<12} {stats2['processes']-stats1['processes']:+d}
{'활용률 (%)':<15} {stats1['utilization']:<12.1f} {stats2['utilization']:<12.1f} {stats2['utilization']-stats1['utilization']:+.1f}
{'배치 너비':<15} {stats1['layout_width']:<12.0f} {stats2['layout_width']:<12.0f} {stats2['layout_width']-stats1['layout_width']:+.0f}
{'배치 높이':<15} {stats1['layout_height']:<12.0f} {stats2['layout_height']:<12.0f} {stats2['layout_height']-stats1['layout_height']:+.0f}
{'회전 공정':<15} {stats1['rotated']:<12} {stats2['rotated']:<12} {stats2['rotated']-stats1['rotated']:+d}
{'적합도':<15} {solution1['fitness']:<12.2f} {solution2['fitness']:<12.2f} {solution2['fitness']-solution1['fitness']:+.2f}

배치 코드:
솔루션 #1: {solution1.get('code', 'N/A')}
솔루션 #2: {solution2.get('code', 'N/A')}
        """
        
        ax.text(0.05, 0.95, comparison_text.strip(), transform=ax.transAxes,
               fontsize=9, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', alpha=0.5))
    
    def _save_results(self, event):
        """결과 저장"""
        if not self.solutions:
            print("❌ 저장할 결과가 없습니다.")
            return
        
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # 이미지 저장
            img_filename = f"optimization_results_{timestamp}.png"
            plt.savefig(img_filename, dpi=300, bbox_inches='tight')
            
            # JSON 저장
            import json
            json_filename = f"optimization_results_{timestamp}.json"
            
            # 직렬화 가능한 형태로 변환
            serializable_solutions = []
            for solution in self.solutions:
                serializable_solution = {
                    'fitness': solution['fitness'],
                    'code': solution.get('code', ''),
                    'method': solution.get('method', ''),
                    'generation': solution.get('generation', ''),
                    'layout': [
                        {
                            'id': rect['id'],
                            'x': rect['x'],
                            'y': rect['y'],
                            'width': rect['width'],
                            'height': rect['height'],
                            'rotated': rect.get('rotated', False),
                            'building_type': rect.get('building_type', 'sub')
                        }
                        for rect in solution['layout']
                    ]
                }
                serializable_solutions.append(serializable_solution)
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'site_dimensions': {'width': self.site_width, 'height': self.site_height},
                    'solutions': serializable_solutions
                }, f, indent=2, ensure_ascii=False)
            
            print(f"💾 결과 저장 완료:")
            print(f"   이미지: {img_filename}")
            print(f"   데이터: {json_filename}")
            
        except Exception as e:
            print(f"❌ 결과 저장 실패: {str(e)}")
    
    def _generate_report(self, event):
        """상세 리포트 생성"""
        if not self.solutions:
            print("❌ 리포트 생성할 결과가 없습니다.")
            return
        
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_filename = f"optimization_report_{timestamp}.txt"
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("공정 배치 최적화 결과 리포트\n")
                f.write("=" * 60 + "\n")
                f.write(f"생성 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"부지 크기: {self.site_width} × {self.site_height} mm\n")
                f.write(f"분석된 솔루션 수: {len(self.solutions)}개\n\n")
                
                # 솔루션별 상세 정보
                for i, solution in enumerate(self.solutions, 1):
                    f.write(f"[솔루션 #{i}]\n")
                    f.write(f"적합도: {solution['fitness']:.2f}점\n")
                    f.write(f"생성 방법: {solution.get('method', 'unknown')}\n")
                    f.write(f"배치 코드: {solution.get('code', 'N/A')}\n")
                    
                    layout = solution['layout']
                    f.write(f"공정 수: {len(layout)}개\n")
                    
                    # 공정 목록
                    f.write("공정 목록:\n")
                    for rect in layout:
                        rotation_str = " (90도 회전)" if rect.get('rotated', False) else ""
                        f.write(f"  - {rect['id']}: {rect['width']}×{rect['height']}mm "
                               f"@ ({rect['x']}, {rect['y']}){rotation_str}\n")
                    
                    f.write("\n" + "-" * 40 + "\n\n")
                
                # 요약 통계
                f.write("[요약 통계]\n")
                if self.solutions:
                    fitnesses = [s['fitness'] for s in self.solutions]
                    f.write(f"최고 적합도: {max(fitnesses):.2f}점\n")
                    f.write(f"최저 적합도: {min(fitnesses):.2f}점\n")
                    f.write(f"평균 적합도: {sum(fitnesses)/len(fitnesses):.2f}점\n")
                
                f.write("\n" + "=" * 60 + "\n")
            
            print(f"📋 리포트 생성 완료: {report_filename}")
            
        except Exception as e:
            print(f"❌ 리포트 생성 실패: {str(e)}")


class SimpleResultVisualizer:
    """간단한 콘솔 기반 결과 표시기"""
    
    def __init__(self, site_width: int, site_height: int):
        self.site_width = site_width
        self.site_height = site_height
        print(f"📋 간단한 결과 표시기 초기화")
    
    def show_results(self, solutions: List[Dict[str, Any]]):
        """콘솔에 결과 표시"""
        
        if not solutions:
            print("❌ 표시할 솔루션이 없습니다.")
            return
        
        print(f"\n🏆 최적화 결과 ({len(solutions)}개 솔루션)")
        print("=" * 80)
        
        # 상위 4개 상세 표시
        top_4 = solutions[:4]
        print("📊 상위 4개 솔루션 (상세):")
        print("-" * 80)
        
        for i, solution in enumerate(top_4, 1):
            layout = solution['layout']
            fitness = solution['fitness']
            code = solution.get('code', 'N/A')
            method = solution.get('method', 'unknown')
            
            print(f"#{i}. 적합도: {fitness:.2f}점 | 방법: {method} | 코드: {code}")
            
            # 공정 목록
            main_processes = [r for r in layout if r.get('building_type') == 'main']
            sub_processes = [r for r in layout if r.get('building_type') == 'sub']
            
            print(f"   공정: 총 {len(layout)}개 (주공정 {len(main_processes)}개, 부공정 {len(sub_processes)}개)")
            
            # 주공정 순서
            if main_processes:
                main_processes.sort(key=lambda x: x.get('main_process_sequence', 999))
                main_sequence = ' → '.join([p['id'] for p in main_processes])
                print(f"   주공정 순서: {main_sequence}")
            
            print()
        
        # 나머지 간단히 표시
        if len(solutions) > 4:
            remaining = solutions[4:8]
            print("📋 나머지 솔루션 (요약):")
            print("-" * 40)
            
            for i, solution in enumerate(remaining, 5):
                fitness = solution['fitness']
                code = solution.get('code', 'N/A')
                method = solution.get('method', 'unknown')
                
                print(f"#{i}. {fitness:.2f}점 | {method} | {code[:20]}...")
        
        print("=" * 80)


if __name__ == "__main__":
    # 테스트 실행
    print("🧪 ResultVisualizer 테스트")
    
    # 테스트 데이터 생성
    site_width, site_height = 1000, 800
    
    test_solutions = []
    for i in range(6):
        fitness = 1000 - i * 50 + np.random.normal(0, 10)
        solution = {
            'fitness': fitness,
            'code': f'AO-b(50)-BR-c(30)-C{"R" if i%2 else "O"}',
            'method': 'exhaustive_search' if i < 3 else 'genetic_algorithm',
            'generation': i + 1,
            'layout': [
                {'id': 'A', 'x': 100+i*10, 'y': 100+i*5, 'width': 150, 'height': 100, 'building_type': 'main', 'rotated': False, 'main_process_sequence': 1},
                {'id': 'B', 'x': 300+i*15, 'y': 150+i*8, 'width': 200, 'height': 120, 'building_type': 'main', 'rotated': i%2==1, 'main_process_sequence': 2},
                {'id': 'C', 'x': 200+i*12, 'y': 300+i*10, 'width': 180, 'height': 90, 'building_type': 'main', 'rotated': False, 'main_process_sequence': 3},
                {'id': 'W', 'x': 500+i*8, 'y': 200+i*12, 'width': 100, 'height': 80, 'building_type': 'sub', 'rotated': False},
            ]
        }
        test_solutions.append(solution)
    
    try:
        # GUI 시각화기 테스트
        visualizer = ResultVisualizer(site_width, site_height)
        visualizer.show_results(test_solutions)
        
        print("✅ GUI 결과 시각화기 테스트 완료")
        
    except Exception as e:
        print(f"⚠️ GUI 시각화기 테스트 실패: {str(e)}")
        print("콘솔 시각화기로 대체 테스트")
        
        # 콘솔 시각화기 테스트
        simple_visualizer = SimpleResultVisualizer(site_width, site_height)
        simple_visualizer.show_results(test_solutions)
        
        print("✅ 콘솔 결과 시각화기 테스트 완료")