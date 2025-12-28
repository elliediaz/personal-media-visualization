/**
 * 오디오 분석기
 *
 * Web Audio API를 사용한 실시간 오디오 분석
 */

class AudioAnalyzer {
    constructor(options = {}) {
        this.options = {
            fftSize: options.fftSize || 2048,
            smoothingTimeConstant: options.smoothingTimeConstant || 0.8,
            minDecibels: options.minDecibels || -90,
            maxDecibels: options.maxDecibels || -10,
        };

        this.audioContext = null;
        this.analyser = null;
        this.source = null;
        this.dataArray = null;
        this.frequencyData = null;

        this.isInitialized = false;
        this.isPlaying = false;

        // 분석 결과
        this.features = {
            energy: 0,
            bass: 0,
            mid: 0,
            high: 0,
            centroid: 0,
            brightness: 0,
            waveform: null,
            spectrum: null,
        };

        // 주파수 대역 범위 (Hz)
        this.frequencyBands = {
            bass: { min: 20, max: 250 },
            mid: { min: 250, max: 4000 },
            high: { min: 4000, max: 20000 },
        };
    }

    /**
     * 오디오 컨텍스트 초기화
     */
    async init() {
        if (this.isInitialized) return;

        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();

            this.analyser.fftSize = this.options.fftSize;
            this.analyser.smoothingTimeConstant = this.options.smoothingTimeConstant;
            this.analyser.minDecibels = this.options.minDecibels;
            this.analyser.maxDecibels = this.options.maxDecibels;

            const bufferLength = this.analyser.frequencyBinCount;
            this.dataArray = new Uint8Array(bufferLength);
            this.frequencyData = new Float32Array(bufferLength);

            this.features.waveform = new Float32Array(bufferLength);
            this.features.spectrum = new Float32Array(bufferLength);

            this.isInitialized = true;
            console.log('AudioAnalyzer 초기화 완료');
        } catch (error) {
            console.error('AudioAnalyzer 초기화 실패:', error);
            throw error;
        }
    }

    /**
     * 오디오 엘리먼트 연결
     * @param {HTMLAudioElement} audioElement
     */
    connectAudioElement(audioElement) {
        if (!this.isInitialized) {
            console.warn('AudioAnalyzer가 초기화되지 않음');
            return;
        }

        if (this.source) {
            this.source.disconnect();
        }

        this.source = this.audioContext.createMediaElementSource(audioElement);
        this.source.connect(this.analyser);
        this.analyser.connect(this.audioContext.destination);

        console.log('오디오 엘리먼트 연결됨');
    }

    /**
     * 마이크 입력 연결
     */
    async connectMicrophone() {
        if (!this.isInitialized) {
            await this.init();
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.source = this.audioContext.createMediaStreamSource(stream);
            this.source.connect(this.analyser);

            console.log('마이크 연결됨');
        } catch (error) {
            console.error('마이크 연결 실패:', error);
            throw error;
        }
    }

    /**
     * 파일에서 오디오 로드
     * @param {File} file
     */
    async loadFile(file) {
        if (!this.isInitialized) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = async (e) => {
                try {
                    const arrayBuffer = e.target.result;
                    const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

                    if (this.source) {
                        this.source.disconnect();
                    }

                    this.source = this.audioContext.createBufferSource();
                    this.source.buffer = audioBuffer;
                    this.source.connect(this.analyser);
                    this.analyser.connect(this.audioContext.destination);

                    resolve(audioBuffer);
                } catch (error) {
                    reject(error);
                }
            };

            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * 분석 업데이트
     */
    update() {
        if (!this.isInitialized || !this.analyser) return;

        // 시간 도메인 데이터 (파형)
        this.analyser.getByteTimeDomainData(this.dataArray);
        for (let i = 0; i < this.dataArray.length; i++) {
            this.features.waveform[i] = (this.dataArray[i] - 128) / 128;
        }

        // 주파수 도메인 데이터
        this.analyser.getFloatFrequencyData(this.frequencyData);
        for (let i = 0; i < this.frequencyData.length; i++) {
            // dB를 0-1 범위로 변환
            this.features.spectrum[i] = Math.max(0, (this.frequencyData[i] - this.options.minDecibels) /
                (this.options.maxDecibels - this.options.minDecibels));
        }

        // 특성 계산
        this._calculateFeatures();
    }

    _calculateFeatures() {
        const spectrum = this.features.spectrum;
        const sampleRate = this.audioContext ? this.audioContext.sampleRate : 44100;
        const binSize = sampleRate / this.options.fftSize;

        // 에너지 (전체 평균)
        let totalEnergy = 0;
        for (let i = 0; i < spectrum.length; i++) {
            totalEnergy += spectrum[i];
        }
        this.features.energy = totalEnergy / spectrum.length;

        // 주파수 대역별 에너지
        this.features.bass = this._getBandEnergy(spectrum, binSize, this.frequencyBands.bass);
        this.features.mid = this._getBandEnergy(spectrum, binSize, this.frequencyBands.mid);
        this.features.high = this._getBandEnergy(spectrum, binSize, this.frequencyBands.high);

        // Spectral Centroid (주파수 무게 중심)
        let weightedSum = 0;
        let magnitudeSum = 0;

        for (let i = 0; i < spectrum.length; i++) {
            const frequency = i * binSize;
            const magnitude = spectrum[i];
            weightedSum += frequency * magnitude;
            magnitudeSum += magnitude;
        }

        this.features.centroid = magnitudeSum > 0 ? weightedSum / magnitudeSum : 0;

        // Brightness (고주파 비율)
        const midPoint = Math.floor(spectrum.length / 2);
        let highEnergy = 0;
        let lowEnergy = 0;

        for (let i = 0; i < spectrum.length; i++) {
            if (i < midPoint) {
                lowEnergy += spectrum[i];
            } else {
                highEnergy += spectrum[i];
            }
        }

        this.features.brightness = (highEnergy + lowEnergy) > 0 ?
            highEnergy / (highEnergy + lowEnergy) : 0.5;
    }

    _getBandEnergy(spectrum, binSize, band) {
        const startBin = Math.floor(band.min / binSize);
        const endBin = Math.min(Math.ceil(band.max / binSize), spectrum.length);

        let energy = 0;
        let count = 0;

        for (let i = startBin; i < endBin; i++) {
            energy += spectrum[i];
            count++;
        }

        return count > 0 ? energy / count : 0;
    }

    /**
     * 현재 특성 가져오기
     * @returns {Object} 오디오 특성
     */
    getFeatures() {
        return { ...this.features };
    }

    /**
     * 정규화된 특성 가져오기 (0-1 범위)
     * @returns {Object}
     */
    getNormalizedFeatures() {
        return {
            energy: Math.min(1, this.features.energy * 2),
            bass: Math.min(1, this.features.bass * 2),
            mid: Math.min(1, this.features.mid * 2),
            high: Math.min(1, this.features.high * 2),
            centroid: Math.min(1, this.features.centroid / 8000),
            brightness: this.features.brightness,
        };
    }

    /**
     * 재생/일시정지
     */
    async resume() {
        if (this.audioContext && this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }
    }

    /**
     * 리소스 정리
     */
    destroy() {
        if (this.source) {
            this.source.disconnect();
        }
        if (this.analyser) {
            this.analyser.disconnect();
        }
        if (this.audioContext) {
            this.audioContext.close();
        }

        this.isInitialized = false;
    }
}

window.AudioAnalyzer = AudioAnalyzer;
