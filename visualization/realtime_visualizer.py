"""
실시간 시각화 모듈 (논블로킹 버전)
최적화 진행 과정을 비동기적으로 모니터링하고 시각화합니다.
"""

import time
import matplotlib
matplotlib.use('TkAgg')  # 명시적으로 백엔드 설정
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, List, Any, Optional
import threading
import queue
import numpy as np


class RealtimeVisualizer:
    """실시간 최적화 진행 시각화기 (논블로킹 버전)"""
    
    def __init__(self, site_width: int, site_height: int, update_interval: float = 1.0):
        """
        초기화
        
        Args:
            site_width: 부지 너비
            site_height: 부지 높이
            update_interval: 업데이트 간격 (초)
        """
        self.site_width = site_width
        self.site_height = site_height
        self.update_interval = update_interval
        
        # 시각화 상태
        self.is_active = False
        self.current_layout = []
        self.progress_data = {
            'current': 0,
            'total': 0,
            'best_fitness': 0,
            'fitness_history': [],
            'start_time': None
        }
        
        # 스레드 안전한 업데이트 큐
        self.update_queue = queue.Queue()
        self.visualization_thread = None
        
        # 색상 매핑
        self.process_colors = {
            'main': '#FF6B6B',      # 빨강 계열 (주공정)
            'sub': '#4ECDC4',       # 청록 계열 (부공정)
            'fixed': '#95A5A6'      # 회색 (고정구역)
        }
        
        # matplotlib 설정
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']  # 한글 폰트 문제 회피
        plt.rcParams['axes.unicode_minus'] = False
        
        print(f"📺 논블로킹 시각화기 초기화: {site_width}×{site_height}m")
    
    def start_optimization(self):
        """최적화 시각화 시작"""
        self.is_active = True
        self.progress_data['start_time'] = time.time()
        self.progress_data['fitness_history'] = []
        
        # 시각화 스레드 시작
        self.visualization_thread = threading.Thread(target=self._visualization_worker, daemon=True)
        self.visualization_thread.start()
        
        print("📺 논블로킹 시각화 시작")
    
    def stop_optimization(self):
        """최적화 시각화 종료"""
        self.is_active = False
        
        if self.visualization_thread and self.visualization_thread.is_alive():
            self.visualization_thread.join(timeout=2.0)
        
        # matplotlib 창 닫기 (메인 스레드에서)
        try:
            plt.close('all')
        except:
            pass
        
        print("📺 논블로킹 시각화 종료")
    
    def update_progress(self, 
                       current: int, 
                       total: int, 
                       best_fitness: float, 
                       current_layout: List[Dict[str, Any]] = None):
        """
        진행 상황 업데이트 (논블로킹)
        """
        if not self.is_active:
            return
        
        # 업데이트 데이터를 큐에 추가
        update_data = {
            'current': current,
            'total': total,
            'best_fitness': best_fitness,
            'current_layout': current_layout.copy() if current_layout else [],
            'timestamp': time.time()
        }
        
        try:
            self.update_queue.put_nowait(update_data)
        except queue.Full:
            # 큐가 가득 차면 오래된 업데이트 제거
            try:
                self.update_queue.get_nowait()
                self.update_queue.put_nowait(update_data)
            except queue.Empty:
                pass
    
    def _visualization_worker(self):
        """시각화 워커 스레드"""
        
        try:
            # 시각화 창 설정
            self.fig, self.axes = plt.subplots(2, 2, figsize=(14, 9))
            self.fig.suptitle('공정 배치 최적화 실시간 모니터링', fontsize=14, fontweight='bold')
            
            # 초기 설정
            self._setup_plots()
            
            plt.ion()  # 대화형 모드
            plt.show(block=False)
            
            last_update_time = 0
            
            while self.is_active:
                current_time = time.time()
                
                # 업데이트 간격 체크
                if current_time - last_update_time < self.update_interval:
                    time.sleep(0.1)
                    continue
                
                # 큐에서 최신 업데이트 가져오기
                latest_update = None
                while not self.update_queue.empty():
                    try:
                        latest_update = self.update_queue.get_nowait()
                    except queue.Empty:
                        break
                
                if latest_update:
                    self._apply_update(latest_update)
                    self._update_visualization()
                    last_update_time = current_time
                
                time.sleep(0.1)
        
        except Exception as e:
            print(f"⚠️ 시각화 워커 오류: {str(e)}")
        finally:
            try:
                if hasattr(self, 'fig'):
                    plt.close(self.fig)
            except:
                pass
    
    def _setup_plots(self):
        """플롯 초기 설정"""
        
        # 서브플롯 제목
        self.axes[0, 0].set_title('현재 최적 배치')
        self.axes[0, 1].set_title('적합도 진화')
        self.axes[1, 0].set_title('진행률')
        self.axes[1, 1].set_title('통계')
        
        # 배치 플롯 설정
        ax_layout = self.axes[0, 0]
        ax_layout.set_xlim(0, self.site_width)
        ax_layout.set_ylim(0, self.site_height)
        ax_layout.set_aspect('equal')
        ax_layout.grid(True, alpha=0.3)
        ax_layout.set_xlabel('X (m)')
        ax_layout.set_ylabel('Y (m)')
        
        # 적합도 플롯 설정
        ax_fitness = self.axes[0, 1]
        ax_fitness.grid(True, alpha=0.3)
        ax_fitness.set_xlabel('평가 횟수')
        ax_fitness.set_ylabel('적합도')
        
        plt.tight_layout()
    
    def _apply_update(self, update_data):
        """업데이트 데이터 적용"""
        
        self.progress_data['current'] = update_data['current']
        self.progress_data['total'] = update_data['total']
        self.progress_data['best_fitness'] = update_data['best_fitness']
        self.progress_data['fitness_history'].append(update_data['best_fitness'])
        
        if update_data['current_layout']:
            self.current_layout = update_data['current_layout']
    
    def _update_visualization(self):
        """시각화 업데이트"""
        
        try:
            # 1. 현재 배치
            self._update_layout_plot()
            
            # 2. 적합도 진화
            self._update_fitness_plot()
            
            # 3. 진행률
            self._update_progress_plot()
            
            # 4. 통계
            self._update_statistics_plot()
            
            # 화면 업데이트
            self.fig.canvas.draw_idle()  # draw() 대신 draw_idle() 사용
            self.fig.canvas.start_event_loop(0.01)  # 짧은 이벤트 루프
            
        except Exception as e:
            print(f"⚠️ 시각화 업데이트 오류: {str(e)}")
    
    def _update_layout_plot(self):
        """배치 플롯 업데이트"""
        
        ax = self.axes[0, 0]
        ax.clear()
        ax.set_title(f'현재 최적 배치 (진행률: {self.progress_data["current"]}/{self.progress_data["total"]})')
        ax.set_xlim(0, self.site_width)
        ax.set_ylim(0, self.site_height)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        
        # 부지 경계
        site_boundary = patches.Rectangle(
            (0, 0), self.site_width, self.site_height,
            linewidth=2, edgecolor='black', facecolor='none'
        )
        ax.add_patch(site_boundary)
        
        # 공정들 표시
        for rect in self.current_layout:
            building_type = rect.get('building_type', 'sub')
            color = self.process_colors.get(building_type, '#CCCCCC')
            
            rectangle = patches.Rectangle(
                (rect['x'], rect['y']), 
                rect['width'], 
                rect['height'],
                linewidth=1,
                edgecolor='black',
                facecolor=color,
                alpha=0.7
            )
            ax.add_patch(rectangle)
            
            # 라벨
            center_x = rect['x'] + rect['width'] / 2
            center_y = rect['y'] + rect['height'] / 2
            rotation_marker = " (R)" if rect.get('rotated', False) else ""
            label = f"{rect['id']}{rotation_marker}"
            
            ax.text(center_x, center_y, label, 
                   ha='center', va='center', 
                   fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.1", facecolor='white', alpha=0.8))
    
    def _update_fitness_plot(self):
        """적합도 플롯 업데이트"""
        
        ax = self.axes[0, 1]
        ax.clear()
        ax.set_title('적합도 진화')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('평가 횟수')
        ax.set_ylabel('적합도')
        
        if self.progress_data['fitness_history']:
            ax.plot(self.progress_data['fitness_history'], 'b-', linewidth=2)
            ax.axhline(y=max(self.progress_data['fitness_history']), color='r', linestyle='--', alpha=0.7)
    
    def _update_progress_plot(self):
        """진행률 플롯 업데이트"""
        
        ax = self.axes[1, 0]
        ax.clear()
        ax.set_title('진행률')
        
        current = self.progress_data['current']
        total = self.progress_data['total']
        
        if total > 0:
            progress = current / total * 100
            ax.barh(['Progress'], [progress], color='green', alpha=0.7)
            ax.set_xlim(0, 100)
            ax.set_xlabel('진행률 (%)')
            
            # 텍스트 표시
            ax.text(progress/2, 0, f'{progress:.1f}%', 
                   ha='center', va='center', fontweight='bold', color='white')
    
    def _update_statistics_plot(self):
        """통계 플롯 업데이트"""
        
        ax = self.axes[1, 1]
        ax.clear()
        ax.set_title('최적화 통계')
        ax.axis('off')
        
        # 텍스트 통계
        if self.progress_data['start_time']:
            elapsed = time.time() - self.progress_data['start_time']
            elapsed_str = f"{elapsed:.1f}s"
        else:
            elapsed_str = "0.0s"
        
        stats_text = f"""
소요 시간: {elapsed_str}
평가된 솔루션: {self.progress_data['current']}
최고 적합도: {self.progress_data['best_fitness']:.2f}
배치된 공정: {len(self.current_layout)}개
        """.strip()
        
        ax.text(0.1, 0.5, stats_text, transform=ax.transAxes, 
               fontsize=12, verticalalignment='center',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.5))


class SimpleConsoleVisualizer:
    """콘솔 기반 간단한 시각화기"""
    
    def __init__(self, site_width: int, site_height: int):
        self.site_width = site_width
        self.site_height = site_height
        self.last_progress = -1
        print(f"📺 콘솔 시각화기 초기화: {site_width}×{site_height}m")
    
    def start_optimization(self):
        print("📺 콘솔 시각화 시작")
        
    def stop_optimization(self):
        print("📺 콘솔 시각화 종료")
    
    def update_progress(self, current, total, best_fitness, current_layout=None):
        if total > 0:
            progress = int(current / total * 100)
            if progress != self.last_progress and progress % 10 == 0:
                print(f"   📊 진행률: {progress}% - 최고 적합도: {best_fitness:.2f}")
                self.last_progress = progress


# 환경에 맞는 시각화기 자동 선택 함수
def create_visualizer(site_width: int, site_height: int, use_gui: bool = True):
    """환경에 맞는 시각화기 생성"""
    
    if not use_gui:
        return SimpleConsoleVisualizer(site_width, site_height)
    
    try:
        # matplotlib 사용 가능 여부 확인
        import matplotlib
        backend = matplotlib.get_backend()
        
        if backend.lower() in ['agg', 'svg', 'pdf', 'ps']:
            print("⚠️ GUI 백엔드가 아닙니다. 콘솔 시각화기를 사용합니다.")
            return SimpleConsoleVisualizer(site_width, site_height)
        
        return RealtimeVisualizer(site_width, site_height)
        
    except (ImportError, Exception) as e:
        print(f"⚠️ GUI 시각화기 초기화 실패: {str(e)}. 콘솔 모드로 전환.")
        return SimpleConsoleVisualizer(site_width, site_height)


if __name__ == "__main__":
    # 테스트
    visualizer = create_visualizer(1000, 800)
    visualizer.start_optimization()
    
    test_layout = [
        {'id': 'A', 'x': 100, 'y': 100, 'width': 150, 'height': 100, 'building_type': 'main'},
    ]
    
    for i in range(1, 21):
        visualizer.update_progress(i, 20, 800 + i * 10, test_layout)
        time.sleep(0.5)
    
    visualizer.stop_optimization()
