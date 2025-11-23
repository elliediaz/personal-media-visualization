"""
API 클라이언트 예제

REST API 및 WebSocket 사용 예제
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import httpx
import websockets

# API 기본 설정
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"


# ===== REST API 예제 =====


class AudioVisualizationClient:
    """오디오 시각화 API 클라이언트"""

    def __init__(self, base_url: str = API_BASE_URL):
        """
        클라이언트 초기화

        Args:
            base_url: API 기본 URL
        """
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=60.0)

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.client.close()

    def upload_audio(self, file_path: Path) -> dict:
        """
        오디오 파일 업로드

        Args:
            file_path: 파일 경로

        Returns:
            업로드 응답
        """
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            response = self.client.post("/api/v1/audio/upload", files=files)
            response.raise_for_status()
            return response.json()

    def get_audio(self, audio_id: str) -> dict:
        """
        오디오 정보 조회

        Args:
            audio_id: 오디오 ID

        Returns:
            오디오 정보
        """
        response = self.client.get(f"/api/v1/audio/{audio_id}")
        response.raise_for_status()
        return response.json()

    def analyze_audio(self, audio_id: str, features: Optional[list] = None) -> dict:
        """
        오디오 분석 요청

        Args:
            audio_id: 오디오 ID
            features: 추출할 특성 목록

        Returns:
            분석 응답
        """
        data = {"audio_id": audio_id, "use_cache": True}
        if features:
            data["features"] = features

        response = self.client.post("/api/v1/analysis/analyze", json=data)
        response.raise_for_status()
        return response.json()

    def get_analysis(self, analysis_id: str) -> dict:
        """
        분석 결과 조회

        Args:
            analysis_id: 분석 ID

        Returns:
            분석 응답
        """
        response = self.client.get(f"/api/v1/analysis/{analysis_id}")
        response.raise_for_status()
        return response.json()

    def wait_for_analysis(self, analysis_id: str, timeout: int = 60) -> dict:
        """
        분석 완료 대기

        Args:
            analysis_id: 분석 ID
            timeout: 타임아웃 (초)

        Returns:
            완료된 분석 응답
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.get_analysis(analysis_id)

            if result["status"] == "completed":
                return result
            elif result["status"] == "failed":
                raise RuntimeError(f"분석 실패: {result.get('error')}")

            time.sleep(1)

        raise TimeoutError("분석 타임아웃")

    def render_visualization(
        self,
        viz_type: str,
        audio_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        width: int = 1920,
        height: int = 1080,
        params: Optional[dict] = None,
    ) -> dict:
        """
        시각화 렌더링 요청

        Args:
            viz_type: 시각화 타입
            audio_id: 오디오 ID
            analysis_id: 분석 ID
            width: 너비
            height: 높이
            params: 추가 파라미터

        Returns:
            시각화 응답
        """
        data = {
            "viz_type": viz_type,
            "width": width,
            "height": height,
        }

        if audio_id:
            data["audio_id"] = audio_id
        if analysis_id:
            data["analysis_id"] = analysis_id
        if params:
            data["params"] = params

        response = self.client.post("/api/v1/visualize/render", json=data)
        response.raise_for_status()
        return response.json()

    def download_visualization(self, viz_id: str, output_path: Path):
        """
        시각화 파일 다운로드

        Args:
            viz_id: 시각화 ID
            output_path: 출력 경로
        """
        response = self.client.get(f"/api/v1/visualize/{viz_id}/download")
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

    def get_presets(self) -> dict:
        """
        프리셋 목록 조회

        Returns:
            프리셋 목록
        """
        response = self.client.get("/api/v1/visualize/presets")
        response.raise_for_status()
        return response.json()


# ===== 사용 예제 =====


def example_basic_workflow():
    """기본 워크플로우 예제"""
    print("=== 기본 API 워크플로우 ===\n")

    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        print(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    with AudioVisualizationClient() as client:
        # 1. 오디오 업로드
        print("1. 오디오 업로드 중...")
        upload_result = client.upload_audio(audio_file)
        audio_id = upload_result["audio_id"]
        print(f"   업로드 완료: {audio_id}\n")

        # 2. 오디오 정보 조회
        print("2. 오디오 정보 조회...")
        audio_info = client.get_audio(audio_id)
        print(f"   파일명: {audio_info['filename']}")
        print(f"   재생 시간: {audio_info['duration']:.2f}초")
        print(f"   샘플링 레이트: {audio_info['sample_rate']}Hz\n")

        # 3. 분석 요청
        print("3. 오디오 분석 중...")
        analysis_result = client.analyze_audio(audio_id)
        analysis_id = analysis_result["analysis_id"]
        print(f"   분석 ID: {analysis_id}")

        # 4. 분석 완료 대기
        print("   분석 완료 대기 중...")
        completed = client.wait_for_analysis(analysis_id, timeout=120)
        print(f"   분석 완료 ({completed['duration']:.2f}초)\n")

        # 5. 시각화 렌더링
        print("4. 시각화 렌더링 중...")

        viz_types = ["waveform", "particles", "circles"]

        for viz_type in viz_types:
            print(f"   - {viz_type} 렌더링...")
            viz_result = client.render_visualization(
                viz_type=viz_type,
                analysis_id=analysis_id,
            )

            viz_id = viz_result["viz_id"]

            # 파일 다운로드
            output_path = Path(f"output/api/{viz_type}.png")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 완료 대기
            import time
            time.sleep(2)

            client.download_visualization(viz_id, output_path)
            print(f"     저장: {output_path}")

        print("\n완료!")


def example_presets():
    """프리셋 사용 예제"""
    print("\n=== 프리셋 예제 ===\n")

    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        print(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    with AudioVisualizationClient() as client:
        # 프리셋 목록 조회
        print("1. 프리셋 목록 조회...")
        presets = client.get_presets()

        print(f"   총 {presets['count']}개 프리셋:\n")
        for preset in presets["presets"]:
            print(f"   - {preset['name']}: {preset['description']}")

        print()

        # 오디오 업로드
        print("2. 오디오 업로드...")
        upload_result = client.upload_audio(audio_file)
        audio_id = upload_result["audio_id"]

        # 프리셋 적용
        print("3. 프리셋 렌더링...")

        for preset in presets["presets"][:3]:  # 처음 3개만
            print(f"   - {preset['name']}...")

            viz_result = client.render_visualization(
                viz_type=preset["viz_type"],
                audio_id=audio_id,
                params=preset["params"],
            )

            viz_id = viz_result["viz_id"]

            # 다운로드
            import time
            time.sleep(2)

            output_path = Path(f"output/api/preset_{preset['name']}.png")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            client.download_visualization(viz_id, output_path)
            print(f"     저장: {output_path}")

        print("\n완료!")


# ===== WebSocket 예제 =====


async def example_websocket_audio_stream():
    """WebSocket 오디오 스트림 예제"""
    print("\n=== WebSocket 오디오 스트림 ===\n")

    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        print(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 오디오 업로드
    with AudioVisualizationClient() as client:
        print("1. 오디오 업로드...")
        upload_result = client.upload_audio(audio_file)
        audio_id = upload_result["audio_id"]
        print(f"   업로드 완료: {audio_id}\n")

    # WebSocket 연결
    print("2. WebSocket 스트림 연결...")
    uri = f"{WS_BASE_URL}/ws/audio/{audio_id}"

    async with websockets.connect(uri) as websocket:
        print("   연결됨\n")

        frame_count = 0

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if data["type"] == "audio":
                    frame_count += 1
                    if frame_count % 100 == 0:
                        print(f"   프레임 {frame_count} 수신...")

                elif data["type"] == "audio_end":
                    total = data["data"]["total_frames"]
                    print(f"\n   스트림 완료: 총 {total} 프레임")
                    break

            except websockets.exceptions.ConnectionClosed:
                break

    print("\n완료!")


async def example_websocket_features():
    """WebSocket 특성 스트림 예제"""
    print("\n=== WebSocket 특성 스트림 ===\n")

    audio_file = Path("data/samples/sample.mp3")

    if not audio_file.exists():
        print(f"샘플 파일을 찾을 수 없습니다: {audio_file}")
        return

    # 오디오 업로드
    with AudioVisualizationClient() as client:
        print("1. 오디오 업로드...")
        upload_result = client.upload_audio(audio_file)
        audio_id = upload_result["audio_id"]
        print(f"   업로드 완료: {audio_id}\n")

    # WebSocket 연결
    print("2. WebSocket 특성 스트림 연결...")
    uri = f"{WS_BASE_URL}/ws/features/{audio_id}"

    async with websockets.connect(uri) as websocket:
        print("   연결됨\n")

        frame_count = 0
        energies = []

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if data["type"] == "features":
                    frame_data = data["data"]
                    frame_count += 1

                    energy = frame_data.get("energy", 0.0)
                    energies.append(energy)

                    if frame_count % 100 == 0:
                        avg_energy = sum(energies) / len(energies)
                        print(
                            f"   프레임 {frame_count}: "
                            f"에너지={energy:.4f}, "
                            f"평균={avg_energy:.4f}"
                        )

                elif data["type"] == "features_end":
                    total = data["data"]["total_frames"]
                    avg_energy = sum(energies) / len(energies) if energies else 0
                    print(f"\n   스트림 완료: 총 {total} 프레임")
                    print(f"   전체 평균 에너지: {avg_energy:.4f}")
                    break

            except websockets.exceptions.ConnectionClosed:
                break

    print("\n완료!")


# ===== 메인 =====


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("Personal Media Visualization API 예제")
    print("=" * 60)

    # REST API 예제
    try:
        example_basic_workflow()
    except Exception as e:
        print(f"기본 워크플로우 에러: {e}")

    try:
        example_presets()
    except Exception as e:
        print(f"프리셋 예제 에러: {e}")

    # WebSocket 예제
    print("\n" + "=" * 60)
    print("WebSocket 예제")
    print("=" * 60)

    try:
        asyncio.run(example_websocket_audio_stream())
    except Exception as e:
        print(f"오디오 스트림 에러: {e}")

    try:
        asyncio.run(example_websocket_features())
    except Exception as e:
        print(f"특성 스트림 에러: {e}")


if __name__ == "__main__":
    main()
