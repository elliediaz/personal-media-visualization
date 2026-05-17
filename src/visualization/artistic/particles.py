"""
파티클 시각화

오디오 반응형 파티클 시스템
"""

import numpy as np

from src.analysis.result import AnalysisResult
from src.utils.logging import get_logger
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer

logger = get_logger(__name__)


class ParticleVisualizer(BaseArtisticVisualizer):
    """파티클 시스템 시각화"""

    def __init__(self, config_override: dict = None):
        """
        ParticleVisualizer 초기화

        Args:
            config_override: 설정 오버라이드
        """
        super().__init__(config_override)
        self.particle_history = []
        self.max_trail_length = 10

    def render(
        self,
        result: AnalysisResult,
        num_particles: int = 1000,
        enable_trails: bool = False,
        trail_length: int = 5,
        particle_mode: str = "scatter",
        time: float = 0.0,
        **kwargs
    ):
        """
        파티클 시각화 렌더링

        Args:
            result: 분석 결과
            num_particles: 파티클 수
            enable_trails: 트레일 효과 활성화
            trail_length: 트레일 길이
            particle_mode: 파티클 모드 ("scatter", "flow", "explosion", "orbit")
            time: 애니메이션 시간
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 오디오 반응형 파라미터
        energy = self.get_audio_reactive_value(result, "energy")
        centroid = self.get_audio_reactive_value(result, "centroid")
        brightness = self.get_audio_reactive_value(result, "brightness")

        # 파티클 수 조절 (에너지 기반)
        adjusted_particles = int(num_particles * (0.5 + energy))

        # 파티클 모드에 따른 위치 생성
        if particle_mode == "flow":
            x, y, velocities = self._generate_flow_particles(
                adjusted_particles, time, energy, centroid
            )
        elif particle_mode == "explosion":
            x, y, velocities = self._generate_explosion_particles(
                adjusted_particles, time, energy
            )
        elif particle_mode == "orbit":
            x, y, velocities = self._generate_orbit_particles(
                adjusted_particles, time, centroid, brightness
            )
        else:
            x, y, velocities = self._generate_scatter_particles(
                adjusted_particles, energy
            )

        # 오디오 반응형 크기
        energy_values = result.timbre.get("rms_energy")
        if energy_values is not None:
            frame_indices = np.random.randint(0, len(energy_values), adjusted_particles)
            base_sizes = energy_values[frame_indices] * 300 + 5
            # 에너지에 따른 크기 펄스
            pulse = 1.0 + energy * 0.5 * np.sin(time * 10)
            sizes = base_sizes * pulse
        else:
            sizes = np.random.uniform(10, 100, adjusted_particles)

        # 색상 (Spectral centroid 기반)
        colors = self._generate_particle_colors(result, adjusted_particles, time)

        # 트레일 렌더링
        if enable_trails and len(self.particle_history) > 0:
            self._render_trails(trail_length)

        # 현재 위치 저장 (트레일용)
        if enable_trails:
            self.particle_history.append((x.copy(), y.copy(), colors.copy()))
            if len(self.particle_history) > self.max_trail_length:
                self.particle_history.pop(0)

        # 파티클 그리기
        self.ax.scatter(x, y, s=sizes, c=colors, alpha=0.7, edgecolors='none')

        # 속도 벡터 표시 (옵션)
        if kwargs.get("show_velocity", False) and velocities is not None:
            self._render_velocity_vectors(x, y, velocities)

        # 글로우 효과 (고에너지 시)
        if energy > 0.6:
            self._add_glow_effect(x, y, sizes, colors, energy)

        # 축 설정
        self.ax.set_xlim(-1.5, 1.5)
        self.ax.set_ylim(-1.5, 1.5)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        # 제목
        tempo = result.rhythm.get("tempo", 0)
        key = result.harmonic.get("key", "Unknown")
        mode_str = f" ({particle_mode})" if particle_mode != "scatter" else ""
        self.set_title(f"Audio Particles{mode_str} - {tempo:.0f} BPM, Key: {key}")

        logger.info(f"파티클 시각화 완료: {adjusted_particles}개, 모드: {particle_mode}")
        return self.fig

    def _generate_scatter_particles(
        self,
        num_particles: int,
        energy: float
    ) -> tuple:
        """
        기본 산포 파티클 생성

        Args:
            num_particles: 파티클 수
            energy: 에너지 값

        Returns:
            (x, y, velocities) 튜플
        """
        np.random.seed(42)
        angles = np.random.uniform(0, 2 * np.pi, num_particles)
        distances = np.random.exponential(0.3 + energy * 0.2, num_particles)

        x = distances * np.cos(angles)
        y = distances * np.sin(angles)

        return x, y, None

    def _generate_flow_particles(
        self,
        num_particles: int,
        time: float,
        energy: float,
        centroid: float
    ) -> tuple:
        """
        흐름 파티클 생성 (펄린 노이즈 기반)

        Args:
            num_particles: 파티클 수
            time: 시간
            energy: 에너지 값
            centroid: centroid 값

        Returns:
            (x, y, velocities) 튜플
        """
        np.random.seed(42)

        # 초기 위치
        x = np.random.uniform(-1.5, 1.5, num_particles)
        y = np.random.uniform(-1.5, 1.5, num_particles)

        # 흐름 필드 (간단한 소용돌이)
        flow_strength = 2 + centroid * 3
        vx = -y * flow_strength + np.sin(x * 3 + time) * energy
        vy = x * flow_strength + np.cos(y * 3 + time) * energy

        # 시간에 따른 이동
        x += vx * 0.01 * np.sin(time)
        y += vy * 0.01 * np.cos(time)

        # 경계 처리
        x = np.clip(x, -1.5, 1.5)
        y = np.clip(y, -1.5, 1.5)

        velocities = np.column_stack([vx, vy])
        return x, y, velocities

    def _generate_explosion_particles(
        self,
        num_particles: int,
        time: float,
        energy: float
    ) -> tuple:
        """
        폭발 파티클 생성

        Args:
            num_particles: 파티클 수
            time: 시간
            energy: 에너지 값

        Returns:
            (x, y, velocities) 튜플
        """
        np.random.seed(42)

        # 방사형 방향
        angles = np.random.uniform(0, 2 * np.pi, num_particles)

        # 폭발 반경 (시간에 따라 확장)
        explosion_phase = (time % (np.pi * 2)) / (np.pi * 2)
        base_radius = explosion_phase * (1.0 + energy)

        # 개별 속도 변화
        speed_variation = np.random.uniform(0.5, 1.5, num_particles)
        distances = base_radius * speed_variation

        x = distances * np.cos(angles)
        y = distances * np.sin(angles)

        # 속도 벡터
        vx = np.cos(angles) * speed_variation * (1 + energy)
        vy = np.sin(angles) * speed_variation * (1 + energy)

        velocities = np.column_stack([vx, vy])
        return x, y, velocities

    def _generate_orbit_particles(
        self,
        num_particles: int,
        time: float,
        centroid: float,
        brightness: float
    ) -> tuple:
        """
        궤도 파티클 생성

        Args:
            num_particles: 파티클 수
            time: 시간
            centroid: centroid 값
            brightness: 밝기 값

        Returns:
            (x, y, velocities) 튜플
        """
        np.random.seed(42)

        # 다중 궤도
        num_orbits = int(3 + centroid * 5)
        particles_per_orbit = num_particles // num_orbits

        x_list, y_list = [], []

        for orbit_idx in range(num_orbits):
            radius = 0.2 + orbit_idx * 0.25
            orbit_speed = (1 + brightness) / (orbit_idx + 1)

            # 궤도 상의 파티클
            base_angles = np.linspace(0, 2 * np.pi, particles_per_orbit, endpoint=False)
            angles = base_angles + time * orbit_speed

            # 약간의 흔들림
            wobble = np.sin(angles * 3 + time) * 0.05

            orbit_x = (radius + wobble) * np.cos(angles)
            orbit_y = (radius + wobble) * np.sin(angles)

            x_list.extend(orbit_x)
            y_list.extend(orbit_y)

        x = np.array(x_list[:num_particles])
        y = np.array(y_list[:num_particles])

        return x, y, None

    def _generate_particle_colors(
        self,
        result: AnalysisResult,
        num_particles: int,
        time: float
    ) -> list:
        """
        파티클 색상 생성

        Args:
            result: 분석 결과
            num_particles: 파티클 수
            time: 시간

        Returns:
            색상 리스트
        """
        colors = []
        centroid_values = result.spectral.get("spectral_centroid")

        if centroid_values is not None:
            frame_indices = np.random.randint(0, len(centroid_values), num_particles)
            for i, idx in enumerate(frame_indices):
                base_color = self.color_mapper.spectral_centroid_to_color(centroid_values[idx])
                # 시간에 따른 색조 변화
                hue_shift = np.sin(time + i * 0.01) * 0.1
                r = np.clip(base_color[0] + hue_shift, 0, 1)
                g = np.clip(base_color[1] + hue_shift * 0.5, 0, 1)
                b = np.clip(base_color[2] - hue_shift, 0, 1)
                colors.append((r, g, b, base_color[3]))
        else:
            for i in range(num_particles):
                hue = (i / num_particles + time * 0.1) % 1.0
                colors.append((hue, 0.8, 0.9, 0.6))

        return colors

    def _render_trails(self, trail_length: int):
        """
        트레일 렌더링

        Args:
            trail_length: 트레일 길이
        """
        history_len = len(self.particle_history)
        actual_length = min(trail_length, history_len)

        for i in range(actual_length):
            idx = history_len - actual_length + i
            if idx < 0:
                continue

            x, y, colors = self.particle_history[idx]
            alpha = (i + 1) / (actual_length + 1) * 0.3
            sizes = np.ones(len(x)) * 5 * (i + 1) / actual_length

            faded_colors = [(c[0], c[1], c[2], alpha) for c in colors]
            self.ax.scatter(x, y, s=sizes, c=faded_colors, edgecolors='none')

    def _render_velocity_vectors(
        self,
        x: np.ndarray,
        y: np.ndarray,
        velocities: np.ndarray
    ):
        """
        속도 벡터 렌더링

        Args:
            x, y: 파티클 위치
            velocities: 속도 벡터
        """
        scale = 0.05
        self.ax.quiver(
            x, y,
            velocities[:, 0], velocities[:, 1],
            alpha=0.3,
            color='white',
            scale=20,
            width=0.002
        )

    def _add_glow_effect(
        self,
        x: np.ndarray,
        y: np.ndarray,
        sizes: np.ndarray,
        colors: list,
        energy: float
    ):
        """
        글로우 효과 추가

        Args:
            x, y: 파티클 위치
            sizes: 파티클 크기
            colors: 파티클 색상
            energy: 에너지 값
        """
        glow_alpha = (energy - 0.6) * 0.5
        glow_sizes = sizes * 2

        glow_colors = [(c[0], c[1], c[2], glow_alpha * 0.3) for c in colors]
        self.ax.scatter(x, y, s=glow_sizes, c=glow_colors, edgecolors='none')

    def render_animation_frame(
        self,
        result: AnalysisResult,
        frame_index: int,
        total_frames: int,
        **kwargs
    ):
        """
        애니메이션 프레임 렌더링

        Args:
            result: 분석 결과
            frame_index: 현재 프레임 인덱스
            total_frames: 총 프레임 수
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        time = (frame_index / total_frames) * np.pi * 4

        return self.render(
            result,
            time=time,
            enable_trails=kwargs.get("enable_trails", True),
            **kwargs
        )

    def clear_trails(self):
        """트레일 히스토리 초기화"""
        self.particle_history = []
