"""
파동 간섭 시각화

오디오 반응형 파동 간섭 패턴 및 오실로스코프 모드
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from src.analysis.result import AnalysisResult
from src.visualization.artistic.base_artistic import BaseArtisticVisualizer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WaveInterferenceVisualizer(BaseArtisticVisualizer):
    """파동 간섭 패턴 및 오실로스코프 시각화"""

    def render(
        self,
        result: AnalysisResult,
        resolution: int = 500,
        mode: str = "interference",
        time: float = 0.0,
        **kwargs
    ):
        """
        파동 시각화 렌더링

        Args:
            result: 분석 결과
            resolution: 해상도
            mode: 렌더링 모드 ("interference", "oscilloscope", "lissajous", "spectrum_3d")
            time: 애니메이션 시간
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        if mode == "oscilloscope":
            return self._render_oscilloscope(result, time, **kwargs)
        elif mode == "lissajous":
            return self._render_lissajous(result, time, **kwargs)
        elif mode == "spectrum_3d":
            return self._render_spectrum_3d(result, time, **kwargs)
        else:
            return self._render_interference(result, resolution, time, **kwargs)

    def _render_interference(
        self,
        result: AnalysisResult,
        resolution: int,
        time: float,
        **kwargs
    ):
        """
        파동 간섭 시각화 렌더링

        Args:
            result: 분석 결과
            resolution: 해상도
            time: 시간
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 그리드 생성
        x = np.linspace(-2, 2, resolution)
        y = np.linspace(-2, 2, resolution)
        X, Y = np.meshgrid(x, y)

        # 오디오 반응형 파라미터
        energy = self.get_audio_reactive_value(result, "energy")
        centroid_val = self.get_audio_reactive_value(result, "centroid")

        # 파동 소스 위치 (onset 기반)
        onset_times = result.rhythm.get("onset_times")

        if onset_times is not None and len(onset_times) > 0:
            num_sources = min(8, len(onset_times))
            sources = []

            for i in range(num_sources):
                angle = (onset_times[i] / result.duration) * 2 * np.pi + time * 0.5
                radius = 1.0 + np.sin(time + i) * 0.2 * energy

                x_pos = radius * np.cos(angle)
                y_pos = radius * np.sin(angle)
                sources.append((x_pos, y_pos))
        else:
            num_sources = 6
            sources = []
            for i in range(num_sources):
                angle = i * (2 * np.pi / num_sources) + time * 0.3
                sources.append((np.cos(angle), np.sin(angle)))

        # 파동 계산
        Z = np.zeros_like(X)

        tempo = result.rhythm.get("tempo", 120)
        frequency = tempo / 60.0

        for i, (sx, sy) in enumerate(sources):
            distance = np.sqrt((X - sx)**2 + (Y - sy)**2)

            # 시간에 따른 파동 이동
            wave = np.sin(distance * 10 * frequency - time * 3) * np.exp(-distance * 0.5)

            centroid = result.spectral.get("spectral_centroid")
            if centroid is not None:
                phase = (i / num_sources) * np.mean(centroid) / 1000
            else:
                phase = i / num_sources

            Z += wave * np.cos(phase * np.pi) * (0.5 + energy * 0.5)

        Z = Z / (np.max(np.abs(Z)) + 1e-10)

        cmap = kwargs.get("cmap", "twilight")

        im = self.ax.imshow(
            Z,
            extent=[-2, 2, -2, 2],
            cmap=cmap,
            origin='lower',
            interpolation='bilinear',
            alpha=0.9
        )

        for sx, sy in sources:
            glow_size = 8 + energy * 8
            self.ax.plot(sx, sy, 'o', color='white', markersize=glow_size, alpha=0.3)
            self.ax.plot(sx, sy, 'o', color='white', markersize=glow_size * 0.5, alpha=0.8)

        if not kwargs.get("hide_colorbar", False):
            cbar = plt.colorbar(im, ax=self.ax)
            cbar.ax.yaxis.set_tick_params(color=self.fg_color)
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=self.fg_color)

        self.ax.set_aspect('equal')
        self.ax.axis('off')

        self.set_title(f"Wave Interference - {tempo:.0f} BPM")

        logger.info(f"파동 간섭 시각화 완료: {num_sources}개 소스")
        return self.fig

    def _render_oscilloscope(
        self,
        result: AnalysisResult,
        time: float,
        **kwargs
    ):
        """
        오실로스코프 스타일 시각화

        Args:
            result: 분석 결과
            time: 시간
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 오디오 반응형 파라미터
        energy = self.get_audio_reactive_value(result, "energy")
        centroid_val = self.get_audio_reactive_value(result, "centroid")
        brightness = self.get_audio_reactive_value(result, "brightness")

        # 파형 생성
        num_points = kwargs.get("num_points", 1000)
        x = np.linspace(-1, 1, num_points)

        # RMS 에너지 기반 파형
        rms_energy = result.timbre.get("rms_energy")
        if rms_energy is not None and len(rms_energy) > 0:
            # 에너지를 파형 길이로 보간
            energy_interp = self.interpolate_feature(rms_energy, num_points)
            energy_interp = self.normalize_feature(energy_interp)
        else:
            energy_interp = np.ones(num_points) * 0.5

        # 멀티 웨이브 조합
        tempo = result.rhythm.get("tempo", 120)
        freq_base = tempo / 30

        # 기본 파형
        wave1 = np.sin(x * np.pi * freq_base * 2 + time * 5) * energy_interp
        wave2 = np.sin(x * np.pi * freq_base * 3 + time * 3) * 0.5 * centroid_val
        wave3 = np.sin(x * np.pi * freq_base * 5 - time * 2) * 0.3 * brightness

        # 합성
        y = (wave1 + wave2 + wave3) * (0.5 + energy * 0.5)

        # 스타일 옵션
        style = kwargs.get("style", "neon")

        if style == "neon":
            self._draw_neon_oscilloscope(x, y, energy)
        elif style == "classic":
            self._draw_classic_oscilloscope(x, y)
        elif style == "spectrum":
            self._draw_spectrum_oscilloscope(x, y, result)
        else:
            self._draw_neon_oscilloscope(x, y, energy)

        # 그리드 (옵션)
        if kwargs.get("show_grid", True):
            self._draw_oscilloscope_grid()

        # 축 설정
        self.ax.set_xlim(-1.1, 1.1)
        self.ax.set_ylim(-1.5, 1.5)
        self.ax.set_aspect('auto')
        self.ax.axis('off')

        self.set_title(f"Oscilloscope - {tempo:.0f} BPM")

        logger.info("오실로스코프 시각화 완료")
        return self.fig

    def _draw_neon_oscilloscope(
        self,
        x: np.ndarray,
        y: np.ndarray,
        energy: float
    ):
        """
        네온 스타일 오실로스코프

        Args:
            x, y: 좌표
            energy: 에너지 값
        """
        # 글로우 레이어
        for width, alpha in [(8, 0.1), (4, 0.2), (2, 0.4), (1, 0.8)]:
            self.ax.plot(
                x, y,
                color=(0, 1, 0.5),
                linewidth=width,
                alpha=alpha,
                solid_capstyle='round'
            )

        # 하이라이트 (고에너지 시)
        if energy > 0.5:
            highlight_alpha = (energy - 0.5) * 2
            self.ax.plot(
                x, y,
                color='white',
                linewidth=0.5,
                alpha=highlight_alpha * 0.5
            )

    def _draw_classic_oscilloscope(self, x: np.ndarray, y: np.ndarray):
        """
        클래식 오실로스코프 스타일

        Args:
            x, y: 좌표
        """
        # 인광 그린
        self.ax.plot(
            x, y,
            color=(0.2, 1, 0.2),
            linewidth=1.5,
            alpha=0.9
        )

        # 잔상 효과
        self.ax.plot(
            x, y * 0.95,
            color=(0.1, 0.5, 0.1),
            linewidth=2,
            alpha=0.3
        )

    def _draw_spectrum_oscilloscope(
        self,
        x: np.ndarray,
        y: np.ndarray,
        result: AnalysisResult
    ):
        """
        스펙트럼 컬러 오실로스코프

        Args:
            x, y: 좌표
            result: 분석 결과
        """
        # 색상을 위치에 따라 변화
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        # 스펙트럼 기반 색상
        centroid = result.spectral.get("spectral_centroid")
        if centroid is not None:
            colors_interp = self.interpolate_feature(
                self.normalize_feature(centroid),
                len(segments)
            )
        else:
            colors_interp = np.linspace(0, 1, len(segments))

        # 컬러맵 적용
        cmap = plt.cm.plasma
        colors = cmap(colors_interp)

        lc = LineCollection(segments, colors=colors, linewidth=2)
        self.ax.add_collection(lc)

    def _draw_oscilloscope_grid(self):
        """오실로스코프 그리드 그리기"""
        # 수직선
        for i in range(-10, 11, 2):
            x_pos = i / 10
            self.ax.axvline(
                x=x_pos,
                color=(0.2, 0.4, 0.2),
                linewidth=0.5,
                alpha=0.3
            )

        # 수평선
        for i in range(-10, 11, 2):
            y_pos = i / 10 * 1.5
            self.ax.axhline(
                y=y_pos,
                color=(0.2, 0.4, 0.2),
                linewidth=0.5,
                alpha=0.3
            )

        # 중심선 (더 밝게)
        self.ax.axhline(y=0, color=(0.3, 0.6, 0.3), linewidth=1, alpha=0.5)
        self.ax.axvline(x=0, color=(0.3, 0.6, 0.3), linewidth=1, alpha=0.5)

    def _render_lissajous(
        self,
        result: AnalysisResult,
        time: float,
        **kwargs
    ):
        """
        리사주 곡선 시각화

        Args:
            result: 분석 결과
            time: 시간
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        self.create_figure()

        # 오디오 반응형 파라미터
        energy = self.get_audio_reactive_value(result, "energy")
        centroid_val = self.get_audio_reactive_value(result, "centroid")

        # 템포 기반 주파수 비율
        tempo = result.rhythm.get("tempo", 120)
        freq_ratio = int(2 + centroid_val * 5)  # 2:1 ~ 7:1

        # 리사주 곡선 계산
        t = np.linspace(0, 2 * np.pi, 2000)

        freq_x = tempo / 60
        freq_y = freq_x * freq_ratio

        phase = time * 2

        x = np.sin(freq_x * t + phase) * (0.8 + energy * 0.2)
        y = np.sin(freq_y * t) * (0.8 + energy * 0.2)

        # 네온 스타일로 그리기
        for width, alpha in [(6, 0.1), (3, 0.3), (1.5, 0.6), (0.5, 1.0)]:
            self.ax.plot(
                x, y,
                color=(1, 0.3, 0.8),
                linewidth=width,
                alpha=alpha
            )

        # 축 설정
        self.ax.set_xlim(-1.2, 1.2)
        self.ax.set_ylim(-1.2, 1.2)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        self.set_title(f"Lissajous ({freq_ratio}:1) - {tempo:.0f} BPM")

        logger.info(f"리사주 곡선 시각화 완료: 비율 {freq_ratio}:1")
        return self.fig

    def _render_spectrum_3d(
        self,
        result: AnalysisResult,
        time: float,
        **kwargs
    ):
        """
        3D 스펙트럼 워터폴 시각화

        Args:
            result: 분석 결과
            time: 시간
            **kwargs: 추가 옵션

        Returns:
            Figure 객체
        """
        from mpl_toolkits.mplot3d import Axes3D

        # 3D 플롯용 Figure 생성
        self.fig = plt.figure(figsize=(10, 8), facecolor=self.bg_color)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor(self.bg_color)

        # 스펙트로그램 데이터
        spectrogram = result.spectral.get("spectrogram")

        if spectrogram is None:
            logger.warning("스펙트로그램 데이터 없음")
            return self.fig

        # 데이터 서브샘플링
        freq_bins = min(100, spectrogram.shape[0])
        time_bins = min(100, spectrogram.shape[1])

        spec_sub = spectrogram[::spectrogram.shape[0]//freq_bins, ::spectrogram.shape[1]//time_bins]

        # dB 변환
        spec_db = 10 * np.log10(spec_sub + 1e-10)
        spec_db = np.clip(spec_db, -80, 0)
        spec_norm = (spec_db + 80) / 80

        # 3D 서피스
        X = np.arange(spec_norm.shape[1])
        Y = np.arange(spec_norm.shape[0])
        X, Y = np.meshgrid(X, Y)

        # 시간에 따른 회전
        self.ax.view_init(elev=30, azim=time * 20 % 360)

        # 서피스 플롯
        surf = self.ax.plot_surface(
            X, Y, spec_norm,
            cmap='plasma',
            linewidth=0,
            antialiased=True,
            alpha=0.8
        )

        # 축 레이블
        self.ax.set_xlabel('Time', color=self.fg_color)
        self.ax.set_ylabel('Frequency', color=self.fg_color)
        self.ax.set_zlabel('Amplitude', color=self.fg_color)

        # 틱 색상
        self.ax.tick_params(colors=self.fg_color)

        tempo = result.rhythm.get("tempo", 120)
        self.ax.set_title(f"3D Spectrum - {tempo:.0f} BPM", color=self.fg_color)

        logger.info("3D 스펙트럼 시각화 완료")
        return self.fig

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
            **kwargs
        )
