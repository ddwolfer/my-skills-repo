---
name: gen-shader
description: 為 pixi.js v8 遊戲建立自定義 shader 效果（火焰、水波、光暈、扭曲等）。自動生成 GLSL + WGSL 雙版本 Filter 模板，支援 WebGPU 和 WebGL。當使用者需要自定義視覺效果、shader、filter、火焰效果、水波效果、光暈、扭曲、displacement、後處理效果、或提到移植 Godot/ShaderToy shader 時都應觸發。使用方式：/gen-shader games/02-pharaohs-cascade FireEffect
---

# gen-shader

為 pixi.js v8 遊戲生成自定義 shader Filter 元件。自動處理 WebGPU/WebGL 雙版本 shader 需求。

## 關鍵規則（必讀）

### 1. WebGPU 強制規則
SDK 使用 `preference: 'webgpu'`（見 `pixi-svelte/InitialiseApplication.svelte`）。
**Filter 必須同時提供 GlProgram（GLSL）+ GpuProgram（WGSL）**，否則靜默失敗。

### 2. WGSL Vertex Shader 必須用預設
**絕對不要自定義 WGSL vertex shader**。必須使用 pixi-filters 的 byte-for-byte 完全相同的 default vertex 字串。
自定義 vertex 會導致 GpuProgram cache miss → vertex attribute slot 不匹配 → pipeline 建立失敗。

### 3. Filter 需要非零內容
Container 裡必須有可見元素（如 `<Rectangle width={W} height={H} backgroundColor={0x000000} backgroundAlpha={0.01} />`），
Filter 處理的是子元素的渲染輸出，空 Container 沒有像素供 Filter 作用。

## pixi.js v8 Filter 模板

### Svelte 元件結構

```svelte
<script lang="ts">
  import { Container, Rectangle } from 'pixi-svelte';
  import { Filter, GlProgram, GpuProgram, Ticker } from 'pixi.js';
  import { onMount } from 'svelte';
  import { getContext } from '../game/context';

  const context = getContext();

  // ===== 可調參數 =====
  const EFFECT_X = 0.5;  // 位置（canvas 比例）
  const EFFECT_Y = 0.5;
  const AREA_W = 150;    // 渲染區域（px）
  const AREA_H = 200;

  // ---- GLSL Fragment (WebGL) ----
  const glVertex = `（見下方 Default GLSL Vertex）`;
  const glFragment = `precision highp float;
in vec2 vTextureCoord;
out vec4 finalColor;
uniform sampler2D uTexture;
uniform float uTime;

void main(void) {
    vec2 uv = vTextureCoord;
    // 你的 shader 邏輯
    vec4 color = texture(uTexture, uv);
    finalColor = color;
}`;

  // ---- WGSL Fragment (WebGPU) ----
  const wgslVertex = `（見下方 Default WGSL Vertex — 必須 byte-for-byte 相同）`;
  const wgslFragment = `struct EffectUniforms {
  uTime: f32,
};

@group(0) @binding(1) var uTexture: texture_2d<f32>;
@group(0) @binding(2) var uSampler: sampler;
@group(1) @binding(0) var<uniform> effectUniforms: EffectUniforms;

@fragment
fn mainFragment(
  @builtin(position) position: vec4<f32>,
  @location(0) uv : vec2<f32>
) -> @location(0) vec4<f32> {
    let color = textureSample(uTexture, uSampler, uv);
    // 你的 shader 邏輯
    return color;
}`;

  // ---- Filter 建立 ----
  const glProgram = GlProgram.from({ vertex: glVertex, fragment: glFragment, name: 'effect-name' });
  const gpuProgram = GpuProgram.from({
    vertex: { source: wgslVertex, entryPoint: 'mainVertex' },
    fragment: { source: wgslFragment, entryPoint: 'mainFragment' },
  });

  const filter = new Filter({
    glProgram,
    gpuProgram,
    resources: {
      effectUniforms: {
        uTime: { value: 0, type: 'f32' },
      },
    },
    padding: 20,
  });

  // ---- Ticker 動畫 ----
  onMount(() => {
    const ticker = Ticker.shared;
    const tickFn = () => {
      filter.resources.effectUniforms.uniforms.uTime = ticker.lastTime * 0.001;
    };
    ticker.add(tickFn);
    return () => ticker.remove(tickFn);
  });

  const canvasW = $derived(context.stateLayoutDerived.canvasSizes().width);
  const canvasH = $derived(context.stateLayoutDerived.canvasSizes().height);
</script>

<Container
  x={canvasW * EFFECT_X - AREA_W / 2}
  y={canvasH * EFFECT_Y - AREA_H / 2}
  zIndex={-1}
  filters={[filter]}
>
  <Rectangle width={AREA_W} height={AREA_H} backgroundColor={0x000000} backgroundAlpha={0.01} />
</Container>
```

### Default GLSL Vertex（WebGL）

```glsl
in vec2 aPosition;
out vec2 vTextureCoord;
uniform vec4 uInputSize;
uniform vec4 uOutputFrame;
uniform vec4 uOutputTexture;

vec4 filterVertexPosition(void) {
    vec2 position = aPosition * uOutputFrame.zw + uOutputFrame.xy;
    position.x = position.x * (2.0 / uOutputTexture.x) - 1.0;
    position.y = position.y * (2.0*uOutputTexture.z / uOutputTexture.y) - uOutputTexture.z;
    return vec4(position, 0.0, 1.0);
}

vec2 filterTextureCoord(void) {
    return aPosition * (uOutputFrame.zw * uInputSize.zw);
}

void main(void) {
    gl_Position = filterVertexPosition();
    vTextureCoord = filterTextureCoord();
}
```

### Default WGSL Vertex（WebGPU — 必須完全相同）

**重要：下方字串必須 byte-for-byte 與 pixi-filters `default2.mjs` 相同，否則 GpuProgram cache miss 會導致 pipeline 失敗。**

在程式碼中直接使用這個 escaped 字串：

```typescript
const wgslVertex = "struct GlobalFilterUniforms {\n  uInputSize:vec4<f32>,\n  uInputPixel:vec4<f32>,\n  uInputClamp:vec4<f32>,\n  uOutputFrame:vec4<f32>,\n  uGlobalFrame:vec4<f32>,\n  uOutputTexture:vec4<f32>,\n};\n\n@group(0) @binding(0) var<uniform> gfu: GlobalFilterUniforms;\n\nstruct VSOutput {\n    @builtin(position) position: vec4<f32>,\n    @location(0) uv : vec2<f32>\n  };\n\nfn filterVertexPosition(aPosition:vec2<f32>) -> vec4<f32>\n{\n    var position = aPosition * gfu.uOutputFrame.zw + gfu.uOutputFrame.xy;\n\n    position.x = position.x * (2.0 / gfu.uOutputTexture.x) - 1.0;\n    position.y = position.y * (2.0*gfu.uOutputTexture.z / gfu.uOutputTexture.y) - gfu.uOutputTexture.z;\n\n    return vec4(position, 0.0, 1.0);\n}\n\nfn filterTextureCoord( aPosition:vec2<f32> ) -> vec2<f32>\n{\n    return aPosition * (gfu.uOutputFrame.zw * gfu.uInputSize.zw);\n}\n\nfn globalTextureCoord( aPosition:vec2<f32> ) -> vec2<f32>\n{\n  return  (aPosition.xy / gfu.uGlobalFrame.zw) + (gfu.uGlobalFrame.xy / gfu.uGlobalFrame.zw);  \n}\n\nfn getSize() -> vec2<f32>\n{\n  return gfu.uGlobalFrame.zw;\n}\n  \n@vertex\nfn mainVertex(\n  @location(0) aPosition : vec2<f32>, \n) -> VSOutput {\n  return VSOutput(\n   filterVertexPosition(aPosition),\n   filterTextureCoord(aPosition)\n  );\n}";
```

## GLSL ↔ WGSL 轉換規則

| GLSL | WGSL |
|------|------|
| `uniform float x;` | `struct U { x: f32 }; @group(1) @binding(0) var<uniform> u: U;` |
| `uniform vec3 c;` | `c: vec3<f32>` in struct |
| `in vec2 vTextureCoord;` | `@location(0) uv: vec2<f32>` in fn params |
| `out vec4 finalColor;` | `-> @location(0) vec4<f32>` return type |
| `texture(uTexture, uv)` | `textureSample(uTexture, uSampler, uv)` |
| `gl_FragColor = ...` | `return vec4<f32>(...)` |
| `float x = 0.0;` | `var x: f32 = 0.0;` 或 `let x: f32 = 0.0;` |
| `vec2(a, b)` | `vec2<f32>(a, b)` |
| `for (float i = 0.0; i < N; i++)` | `for (var i: f32 = 0.0; i < N; i += 1.0)` |
| `float func(float x) { return x; }` | `fn func(x: f32) -> f32 { return x; }` |

## Godot Shader → pixi.js 移植 Checklist

1. ✅ 移除 `shader_type canvas_item;`
2. ✅ `TIME` → `uTime` uniform（透過 ticker 更新）
3. ✅ `UV` → `vTextureCoord`（GLSL）/ `uv` param（WGSL）
4. ✅ `COLOR = vec4(...)` → `finalColor = vec4(...)`（GLSL）/ `return vec4<f32>(...)`（WGSL）
5. ✅ `hint_range(min, max)` → 移除，改用 JS 常數
6. ✅ `source_color` → 移除，uniform 值用 `Float32Array`
7. ✅ `saturate(x)` → 自定義函數 `clamp(x, 0.0, 1.0)`（WGSL 無 saturate）
8. ✅ 降低 particleCount（128→40-60）適應瀏覽器效能
9. ✅ 用 `max(ct, 0.001)` 保護 `log()` 避免 NaN

## Uniform 綁定模式

### resources 定義
```typescript
resources: {
  myUniforms: {  // ← 這個名稱必須與 WGSL 的 struct 名對應
    uTime: { value: 0, type: 'f32' },
    uColor: { value: new Float32Array([1.0, 0.5, 0.0]), type: 'vec3<f32>' },
    uScale: { value: new Float32Array([1.0, 1.0]), type: 'vec2<f32>' },
  },
},
```

### Ticker 更新
```typescript
filter.resources.myUniforms.uniforms.uTime = ticker.lastTime * 0.001;
```

## 完整範例

參考 `games/02-pharaohs-cascade/src/components/FlameEffect.svelte`（移植自 Godot torch shader）。

## 流程

1. 使用者描述需要的視覺效果
2. 讀取目標遊戲的 Game.svelte 了解現有元件結構
3. 寫 GLSL fragment shader
4. 翻譯為 WGSL fragment shader
5. 用上方模板組裝 Svelte 元件
6. 加入 Game.svelte（通常在 Background 之後）
7. 用 ticker 驅動動畫 uniform
