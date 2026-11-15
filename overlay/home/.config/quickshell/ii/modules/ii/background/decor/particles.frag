#version 440

layout(location = 0) in vec2 vUv;
layout(location = 1) in vec4 vColor;
layout(location = 2) in vec3 vInfo;

layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float time;
    float kind;
    float cols;
    float cells;
    float seed;
    vec2 field;
};

layout(binding = 1) uniform sampler2D atlas;

void main() {
    float a = vInfo.z * qt_Opacity;
    if (vInfo.x < 0.5) {
        vec2 uv = vec2((vInfo.y * 104.0 + 4.0 + vUv.x * 96.0) / (cells * 104.0),
                       (4.0 + vUv.y * 96.0) / 104.0);
        fragColor = texture(atlas, uv) * a;
    } else {
        float cover;
        if (vInfo.x < 1.5) {
            float dist = length(vUv - 0.5) * (vColor.a + 2.0);
            cover = clamp(vColor.a * 0.5 - dist + 0.5, 0.0, 1.0);
        } else {
            float dist = abs(vUv.x - 0.5) * 3.6;
            cover = clamp(vColor.a * 0.5 - dist + 0.5, 0.0, 1.0);
        }
        fragColor = vec4(vColor.rgb, 1.0) * cover * a;
    }
}
