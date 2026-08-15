"use client";

import * as React from "react";

const VERTEX_SRC = `
attribute vec2 aPosition;
void main() {
  gl_Position = vec4(aPosition, 0.0, 1.0);
}
`;

// Rippling, chromatically-dispersed concentric rings -- the topology.vc
// "chrome water" hero, live and generative (a real fragment shader, not a
// blurred static image), fused with our own product mechanism: the ring
// origin drifts and pulses with the same restless quality as the concept
// graph it sits behind, and it's mouse-reactive for "more interactive
// components".
const FRAGMENT_SRC = `
precision highp float;
uniform vec2 uResolution;
uniform float uTime;
uniform vec2 uMouse;
uniform vec3 uBase;
uniform vec3 uTint;
uniform float uIntensity;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * uResolution) / min(uResolution.x, uResolution.y);

  vec2 center = uMouse * 0.5;
  center += 0.18 * vec2(sin(uTime * 0.07), cos(uTime * 0.05));

  vec2 p = uv - center;
  float dist = length(p);
  float ang = atan(p.y, p.x);

  float warp = noise(p * 2.4 + uTime * 0.06) * 0.35;
  warp += noise(p * 6.0 - uTime * 0.03) * 0.12;
  float d = dist + warp * 0.22 + 0.05 * sin(ang * 3.0 + uTime * 0.4);

  float ringFreq = 26.0;
  float speed = uTime * 0.65;

  float rR = sin(d * ringFreq - speed) * 0.5 + 0.5;
  float rG = sin(d * ringFreq * 1.015 - speed) * 0.5 + 0.5;
  float rB = sin(d * ringFreq * 1.03 - speed) * 0.5 + 0.5;

  rR = pow(rR, 2.2);
  rG = pow(rG, 2.2);
  rB = pow(rB, 2.2);

  float falloff = smoothstep(1.05, 0.05, dist);
  float core = smoothstep(0.7, 0.0, dist) * 0.6;

  vec3 rings = vec3(rR, rG, rB);
  vec3 color = uBase + rings * uTint * (falloff * uIntensity) + core * uTint * 0.5;

  gl_FragColor = vec4(color, 1.0);
}
`;

function compileShader(gl: WebGLRenderingContext, type: number, source: string) {
  const shader = gl.createShader(type);
  if (!shader) return null;
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    gl.deleteShader(shader);
    return null;
  }
  return shader;
}

interface LiquidChromeProps {
  className?: string;
  /** 0-1, how strong the ring/chroma pattern reads against the base. */
  intensity?: number;
}

export function LiquidChrome({ className, intensity = 1 }: LiquidChromeProps) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);
  const mouseRef = React.useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const gl = (canvas.getContext("webgl") ||
      canvas.getContext("experimental-webgl")) as WebGLRenderingContext | null;
    if (!gl) return;

    const vertexShader = compileShader(gl, gl.VERTEX_SHADER, VERTEX_SRC);
    const fragmentShader = compileShader(gl, gl.FRAGMENT_SHADER, FRAGMENT_SRC);
    if (!vertexShader || !fragmentShader) return;

    const program = gl.createProgram();
    if (!program) return;
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return;
    gl.useProgram(program);

    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 3, -1, -1, 3]),
      gl.STATIC_DRAW
    );
    const aPosition = gl.getAttribLocation(program, "aPosition");
    gl.enableVertexAttribArray(aPosition);
    gl.vertexAttribPointer(aPosition, 2, gl.FLOAT, false, 0, 0);

    const uResolution = gl.getUniformLocation(program, "uResolution");
    const uTime = gl.getUniformLocation(program, "uTime");
    const uMouse = gl.getUniformLocation(program, "uMouse");
    const uBase = gl.getUniformLocation(program, "uBase");
    const uTint = gl.getUniformLocation(program, "uTint");
    const uIntensity = gl.getUniformLocation(program, "uIntensity");

    let raf = 0;
    let start = performance.now();
    const dpr = Math.min(window.devicePixelRatio || 1, 1.75);

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas.height = Math.max(1, Math.floor(rect.height * dpr));
      gl.viewport(0, 0, canvas.width, canvas.height);
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(canvas);

    const handlePointerMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current.targetX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      mouseRef.current.targetY = -((e.clientY - rect.top) / rect.height - 0.5) * 2;
    };
    window.addEventListener("pointermove", handlePointerMove);

    const readTint = () => {
      const isDark = document.documentElement.classList.contains("dark");
      // near-black / near-white bases, teal-tinted rings either way --
      // keeps the same material in both themes, per the token system.
      return isDark
        ? { base: [0.03, 0.03, 0.025], tint: [0.13, 0.55, 0.58] }
        : { base: [0.05, 0.05, 0.04], tint: [0.12, 0.55, 0.58] };
    };

    const render = (now: number) => {
      const t = (now - start) / 1000;
      mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.04;
      mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.04;

      const { base, tint } = readTint();
      gl.uniform2f(uResolution, canvas.width, canvas.height);
      gl.uniform1f(uTime, reducedMotion ? t * 0.15 : t);
      gl.uniform2f(uMouse, mouseRef.current.x, mouseRef.current.y);
      gl.uniform3f(uBase, base[0], base[1], base[2]);
      gl.uniform3f(uTint, tint[0], tint[1], tint[2]);
      gl.uniform1f(uIntensity, intensity);
      gl.drawArrays(gl.TRIANGLES, 0, 3);

      raf = requestAnimationFrame(render);
    };
    raf = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
      window.removeEventListener("pointermove", handlePointerMove);
      gl.deleteProgram(program);
      gl.deleteShader(vertexShader);
      gl.deleteShader(fragmentShader);
      gl.deleteBuffer(buffer);
    };
  }, [intensity]);

  return <canvas ref={canvasRef} className={className} aria-hidden />;
}
