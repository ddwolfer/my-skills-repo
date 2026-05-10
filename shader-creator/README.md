# Shader Creator Skill

A Claude skill for creating interactive GLSL shaders with real-time parameter controls.

## What It Does

This skill helps you create GPU-accelerated visual effects using GLSL fragment shaders. It generates:

1. **Shader Concept** (.md file) - A visual philosophy describing the shader aesthetic
2. **Interactive Viewer** (.html file) - Self-contained HTML with Three.js and live parameter controls

## When to Use

Use this skill when you want to create:
- Procedural textures and patterns
- Animated visual effects
- Shader art and generative graphics
- Real-time GPU-accelerated visuals
- Interactive shader experiments

## How It Works

1. **Describe your vision** - Tell Claude what kind of shader you want
2. **Shader concept is created** - A 4-6 paragraph description of the visual aesthetic
3. **GLSL implementation** - Fragment shader code that brings the concept to life
4. **Interactive viewer** - HTML artifact with parameter controls for real-time exploration

## Features

- **Real-time rendering** at 60fps using WebGL
- **Interactive parameters** with sliders and color pickers
- **Self-contained HTML** - works immediately in browser or Claude artifacts
- **Download capability** - save current frame as PNG
- **Responsive design** - adapts to different screen sizes

## Example Shaders

The skill can create various shader types:

- **Plasma Waves** - Undulating energy fields with sine wave interference
- **Fractal Noise** - Self-similar patterns using FBM (Fractional Brownian Motion)
- **Ray Marching** - 3D shapes rendered from distance functions
- **Voronoi Cells** - Organic cellular patterns
- **Kaleidoscope** - Radial symmetry and reflections
- **Glitch Effects** - Digital distortion and chromatic aberration
- **And many more...**

## Technical Details

- Uses **Three.js** for WebGL setup
- **GLSL ES 1.0** fragment shaders
- **Uniforms** for parameters (u_time, u_resolution, custom params)
- **Real-time updates** when parameters change
- **Optimized** for 60fps performance

## Files

- `SKILL.md` - Main skill definition and instructions
- `LICENSE.txt` - MIT License
- `templates/example-plasma.html` - Example plasma waves shader
- `README.md` - This file

## Usage Example

```
User: "Create a shader with flowing rainbow colors"

Claude:
1. Creates shader concept describing rainbow flow aesthetic
2. Implements GLSL shader with HSV color cycling
3. Generates HTML artifact with speed, hue shift, and saturation controls
4. User can adjust parameters in real-time and download results
```

## License

MIT License - See LICENSE.txt for details
