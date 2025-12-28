/**
 * CRT 프래그먼트 셰이더
 * 스캔라인, RGB 색수차, 노이즈, 비네트 효과 통합
 */

precision mediump float;

varying vec2 vTextureCoord;

uniform sampler2D uSampler;
uniform vec2 uResolution;
uniform float uTime;

// 효과 파라미터
uniform float uScanlineIntensity;
uniform float uScanlineCount;
uniform float uChromaticOffset;
uniform float uNoiseIntensity;
uniform float uVignetteIntensity;
uniform float uVignetteRadius;
uniform float uBloomIntensity;
uniform float uCurvature;

// 랜덤 노이즈 생성
float random(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

// 화면 곡률 (배럴 왜곡)
vec2 curveCoords(vec2 uv) {
    if (uCurvature <= 0.0) return uv;

    vec2 curved = uv * 2.0 - 1.0;
    float r2 = curved.x * curved.x + curved.y * curved.y;
    curved *= 1.0 + uCurvature * r2;
    return curved * 0.5 + 0.5;
}

// RGB 색수차
vec3 chromaticAberration(vec2 uv) {
    float offset = uChromaticOffset / uResolution.x;

    // 중심으로부터의 거리에 따라 오프셋 조절
    vec2 center = uv - 0.5;
    float dist = length(center);
    float radialOffset = offset * dist * 2.0;

    float r = texture2D(uSampler, uv + vec2(radialOffset, 0.0)).r;
    float g = texture2D(uSampler, uv).g;
    float b = texture2D(uSampler, uv - vec2(radialOffset, 0.0)).b;

    return vec3(r, g, b);
}

// 스캔라인 효과
float scanlines(vec2 uv) {
    float scanline = sin(uv.y * uScanlineCount * 3.14159) * 0.5 + 0.5;
    return 1.0 - (1.0 - scanline) * uScanlineIntensity;
}

// 비네트 효과
float vignette(vec2 uv) {
    vec2 center = uv - 0.5;
    float dist = length(center);
    float vig = smoothstep(uVignetteRadius, uVignetteRadius - 0.3, dist);
    return mix(1.0, vig, uVignetteIntensity);
}

// 노이즈 효과
float noise(vec2 uv) {
    return random(uv + vec2(uTime * 0.1, 0.0)) * uNoiseIntensity;
}

// 간단한 블룸 (가우시안 블러 근사)
vec3 bloom(vec2 uv, vec3 color) {
    if (uBloomIntensity <= 0.0) return color;

    vec3 bloomColor = vec3(0.0);
    float samples = 4.0;
    float blurSize = 3.0 / uResolution.x;

    for (float x = -samples; x <= samples; x++) {
        for (float y = -samples; y <= samples; y++) {
            vec2 offset = vec2(x, y) * blurSize;
            bloomColor += texture2D(uSampler, uv + offset).rgb;
        }
    }

    bloomColor /= (samples * 2.0 + 1.0) * (samples * 2.0 + 1.0);

    // 밝은 영역만 블룸 적용
    float brightness = dot(bloomColor, vec3(0.299, 0.587, 0.114));
    vec3 bloomMask = bloomColor * smoothstep(0.5, 1.0, brightness);

    return color + bloomMask * uBloomIntensity;
}

void main(void) {
    // 화면 곡률 적용
    vec2 uv = curveCoords(vTextureCoord);

    // 범위 체크
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    // RGB 색수차 적용
    vec3 color = chromaticAberration(uv);

    // 블룸 적용
    color = bloom(uv, color);

    // 스캔라인 적용
    color *= scanlines(uv);

    // 노이즈 적용
    color += vec3(noise(uv) - uNoiseIntensity * 0.5);

    // 비네트 적용
    color *= vignette(uv);

    // 색상 범위 제한
    color = clamp(color, 0.0, 1.0);

    gl_FragColor = vec4(color, 1.0);
}
