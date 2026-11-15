#version 440

layout(location = 0) in vec4 qt_Vertex;
layout(location = 1) in vec2 qt_MultiTexCoord0;

layout(location = 0) out vec2 vUv;
layout(location = 1) out vec4 vColor;
layout(location = 2) out vec3 vInfo;

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

out gl_PerVertex { vec4 gl_Position; };

const float PI = 3.14159265;
const float TAU = 6.28318531;

float hash(float a, float b) {
    return fract(sin(a * 12.9898 + b * 78.233 + seed) * 43758.5453);
}

float pickN(float r, float n) {
    return min(floor(r * n), n - 1.0);
}

float inOutSine(float x) {
    return 0.5 - 0.5 * cos(PI * clamp(x, 0.0, 1.0));
}

vec3 pal5(float k, vec3 a, vec3 b, vec3 c, vec3 d, vec3 e) {
    if (k < 0.5) return a;
    if (k < 1.5) return b;
    if (k < 2.5) return c;
    if (k < 3.5) return d;
    return e;
}

void main() {
    float col = floor(qt_MultiTexCoord0.x * cols + 0.5);
    float row = floor(qt_MultiTexCoord0.y + 0.5);
    float slot = mod(col, 4.0);
    float i = floor(col / 4.0);
    vec2 corner = vec2(slot > 0.5 ? 1.0 : 0.0, row);
    if (slot > 1.5) {
        corner = vec2(1.0, 1.0);
    }
    if (slot > 2.5) {
        i += 1.0;
        corner = vec2(0.0, 0.0);
    }

    float W = field.x;
    float H = field.y;

    vec2 center;
    vec2 quad;
    float rot = 0.0;
    vec2 scl = vec2(1.0);
    float alpha;
    float mode = 0.0;
    float cell = 0.0;
    vec3 tint = vec3(1.0);
    float px = 0.0;

    if (kind > 9.5) {
        float sparkle = step(hash(i, 5.0), 0.22);
        float size = sparkle > 0.5 ? 12.0 + hash(i, 6.0) * 14.0 : 1.5 + hash(i, 6.0) * 2.5;
        float boxW = sparkle > 0.5 ? size : size * 4.0;
        vec2 pos = vec2(hash(i, 7.0) * W, pow(hash(i, 8.0), 1.4) * H * 0.75);
        center = pos + vec2(boxW * 0.5);
        float pause = hash(i, 9.0) * 4.0;
        float up = 1.2 + hash(i, 10.0) * 1.8;
        float down = 1.2 + hash(i, 11.0) * 1.8;
        float t = mod(time + hash(i, 12.0) * 10.0, pause + up + down);
        float tw = t < pause ? 0.0 : (t < pause + up ? inOutSine((t - pause) / up) : 1.0 - inOutSine((t - pause - up) / down));
        alpha = 0.15 + 0.85 * tw;
        if (sparkle > 0.5) {
            float a = 1.8 + hash(i, 13.0) * 1.5;
            float b = 1.8 + hash(i, 14.0) * 1.5;
            float s = mod(time + hash(i, 15.0) * 5.0, a + b);
            float k = s < a ? inOutSine(s / a) : 1.0 - inOutSine((s - a) / b);
            scl = vec2(0.7 + 0.45 * k);
            quad = vec2(size);
            cell = step(hash(i, 16.0), 0.35);
        } else {
            mode = 1.0;
            px = size;
            quad = vec2(size + 2.0);
            tint = hash(i, 17.0) < 0.25 ? vec3(0.961, 0.839, 0.529) : vec3(0.902, 0.914, 1.0);
        }
    } else {
        bool snow = kind > 0.5 && kind < 1.5;
        bool leaves = kind > 1.5 && kind < 3.5;
        bool petals = kind > 3.5 && kind < 4.5;
        bool sand = kind > 4.5 && kind < 5.5;
        bool rain = kind > 5.5 && kind < 6.5;
        bool embers = kind > 6.5 && kind < 7.5;
        bool flies = kind > 7.5 && kind < 8.5;
        bool ocean = kind > 8.5;
        bool bubbles = kind < 0.5;
        bool rising = bubbles || embers || ocean;
        bool tumble = leaves || petals;
        bool jelly = ocean && hash(i, 4.0) < 0.18;

        float depth = 0.45 + 0.55 * hash(i, 1.0);
        float rd = hash(i, 3.0);
        float dur;
        if (snow) dur = (16.0 + rd * 10.0) / depth;
        else if (leaves) dur = (15.0 + rd * 12.0) / depth;
        else if (petals) dur = (18.0 + rd * 12.0) / depth;
        else if (sand) dur = (5.0 + rd * 5.0) / depth;
        else if (rain) dur = (0.65 + rd * 0.55) / depth;
        else if (embers) dur = (7.0 + rd * 7.0) / depth;
        else if (flies) dur = 12.0 + rd * 12.0;
        else if (jelly) dur = (30.0 + rd * 20.0) / depth;
        else if (ocean) dur = (12.0 + rd * 10.0) / depth;
        else dur = (14.0 + rd * 14.0) / depth;

        float cyc = time / dur + hash(i, 2.0);
        float c = floor(cyc);
        float p = cyc - c;
        float ci = i + 0.37;
        float r1 = hash(ci * 1.3 + 11.0, c + 0.1);
        float r2 = hash(ci * 1.7 + 23.0, c + 0.2);
        float r3 = hash(ci * 1.9 + 37.0, c + 0.3);
        float r4 = hash(ci * 2.3 + 41.0, c + 0.4);
        float r5 = hash(ci * 2.9 + 53.0, c + 0.5);
        float r6 = hash(ci * 3.1 + 67.0, c + 0.6);
        float r7 = hash(ci * 3.7 + 71.0, c + 0.7);
        float r8 = hash(ci * 4.1 + 83.0, c + 0.8);

        float sc = 0.6 + r1 * 1.4;
        float sx = r2 * W;
        float sy = r3 * H;
        float size;
        float sway;
        float spin = 0.0;
        float blinks = 3.0;
        float sgn = r6 < 0.5 ? -1.0 : 1.0;

        if (snow) {
            size = (10.0 + r4 * 18.0) * depth;
            sway = (20.0 + r5 * 45.0) * depth;
            spin = sgn * (60.0 + r7 * 180.0);
            cell = pickN(r8, 3.0);
        } else if (leaves) {
            size = (20.0 + r4 * 18.0) * depth;
            sway = (70.0 + r5 * 110.0) * depth;
            spin = sgn * (240.0 + r7 * 420.0);
            cell = pickN(r8, 5.0);
        } else if (petals) {
            size = (12.0 + r4 * 12.0) * depth;
            sway = (60.0 + r5 * 120.0) * depth;
            spin = sgn * (120.0 + r7 * 260.0);
            cell = pickN(r8, 3.0);
        } else if (sand) {
            sy = H * (0.35 + pow(r3, 0.7) * 0.65);
            size = (2.0 + r4 * 3.5) * depth;
            sway = (10.0 + r5 * 40.0) * depth;
            tint = pal5(pickN(r8, 5.0), vec3(0.878, 0.690, 0.478), vec3(0.851, 0.627, 0.400),
                        vec3(0.788, 0.510, 0.306), vec3(0.949, 0.808, 0.588), vec3(0.710, 0.443, 0.247));
        } else if (rain) {
            size = (18.0 + r4 * 30.0) * depth;
            sway = 0.0;
            tint = pal5(pickN(r8, 4.0), vec3(0.243, 0.902, 1.0), vec3(1.0, 0.310, 0.847),
                        vec3(0.788, 0.965, 1.0), vec3(0.541, 0.502, 0.690), vec3(0.0));
        } else if (embers) {
            size = (6.0 + r4 * 12.0) * depth;
            sway = (20.0 + r5 * 60.0) * depth;
            blinks = 4.0 + r7 * 6.0;
            cell = pickN(r8, 3.0);
        } else if (flies) {
            sy = H * (0.3 + r3 * 0.65);
            size = (12.0 + r4 * 14.0) * depth;
            sway = (60.0 + r5 * 140.0) * depth;
            blinks = 2.0 + r7 * 4.0;
        } else if (jelly) {
            size = (44.0 + r4 * 40.0) * depth;
            sway = (20.0 + r5 * 40.0) * depth;
            cell = 2.0 + pickN(r8, 3.0);
        } else if (ocean) {
            size = (8.0 + r4 * 18.0) * depth;
            sway = (12.0 + r5 * 25.0) * depth;
            cell = pickN(r8, 2.0);
        } else {
            size = (14.0 + r4 * 30.0) * depth;
            sway = (12.0 + r5 * 30.0) * depth;
            cell = pickN(r8, 3.0);
        }

        float w = rain ? 1.6 : size;
        float h = size;
        float wave = sin(p * TAU * sc);
        vec2 pos;
        if (sand) pos = vec2(-40.0 + p * (W + 80.0), sy + sway * wave - p * 60.0 * depth);
        else if (rain) pos = vec2(sx - 140.0 + p * 260.0, -60.0 + p * (H + 120.0));
        else if (flies) pos = vec2(sx + sway * wave, sy + sway * 0.6 * cos(p * TAU * sc * 0.7));
        else if (rising) pos = vec2(sx + sway * wave, H + 40.0 - p * (H + 80.0));
        else pos = vec2(sx + sway * wave, -40.0 + p * (H + 80.0));
        center = pos + vec2(w, h) * 0.5;

        rot = rain ? 28.0 : spin * p;

        float d = 0.45 + 0.55 * depth;
        if (embers) alpha = d * (1.0 - p) * (0.55 + 0.45 * abs(sin(p * PI * blinks)));
        else if (flies) alpha = d * (0.08 + 0.92 * pow(max(0.0, sin(p * TAU * blinks)), 2.0));
        else if (rain) alpha = 0.5 * d;
        else if (rising) alpha = 0.95 * (1.0 - p * 0.7) * d;
        else alpha = 0.95 * d;

        if (tumble) scl.x = cos(p * TAU * sc * 2.0);
        if (jelly) scl.y = 1.0 + 0.12 * sin(p * PI * 40.0);
        else if (bubbles || ocean) scl.y = 1.0 + 0.06 * sin(p * PI * 14.0);

        if (sand) {
            mode = 1.0;
            px = size;
            quad = vec2(size + 2.0);
        } else if (rain) {
            mode = 2.0;
            px = 1.6;
            quad = vec2(3.6, h);
        } else {
            quad = vec2(w, h);
        }
    }

    vec2 local = (corner - 0.5) * quad * scl;
    float a = radians(rot);
    float cs = cos(a);
    float sn = sin(a);
    vec2 v = center + vec2(local.x * cs - local.y * sn, local.x * sn + local.y * cs);

    vUv = corner;
    vColor = vec4(tint, px);
    vInfo = vec3(mode, cell, alpha);
    gl_Position = qt_Matrix * vec4(v, 0.0, 1.0);
}
