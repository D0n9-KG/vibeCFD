import { useEffect, useRef, useState } from "react";

import { resolveArtifactUrl } from "../lib/api";
import type { ArtifactItem } from "../lib/types";

interface ModelViewportProps {
  artifact: ArtifactItem;
}

type ViewportState = "loading" | "ready" | "fallback" | "error";

function hasWebGLSupport(): boolean {
  if (typeof navigator !== "undefined" && /jsdom/i.test(navigator.userAgent)) {
    return false;
  }
  try {
    const canvas = document.createElement("canvas");
    const webgl2 = canvas.getContext("webgl2");
    const webgl = webgl2 ?? canvas.getContext("webgl") ?? canvas.getContext("experimental-webgl");
    return webgl !== null;
  } catch {
    return false;
  }
}

export function ModelViewport({ artifact }: ModelViewportProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [viewportState, setViewportState] = useState<ViewportState>("loading");

  useEffect(() => {
    let cancelled = false;
    let animationFrameId = 0;
    let resizeObserver: ResizeObserver | null = null;
    let renderer: any = null;
    let controls: any = null;
    let resizeHandler: (() => void) | null = null;
    const container = hostRef.current;

    async function initialize() {
      if (!container) {
        return;
      }
      if (!hasWebGLSupport()) {
        setViewportState("fallback");
        return;
      }

      try {
        const [THREE, controlsModule, objLoaderModule] = await Promise.all([
          import("three"),
          import("three/examples/jsm/controls/OrbitControls.js"),
          import("three/examples/jsm/loaders/OBJLoader.js")
        ]);

        if (cancelled) {
          return;
        }

        const response = await fetch(resolveArtifactUrl(artifact.url));
        const source = await response.text();
        if (!response.ok) {
          throw new Error(source || "模型文件加载失败");
        }

        const scene = new THREE.Scene();
        scene.background = new THREE.Color("#eef4fa");

        const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 200);
        camera.position.set(7.5, 2.6, 7.2);

        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.domElement.className = "viewport-3d__canvas";
        container.innerHTML = "";
        container.appendChild(renderer.domElement);

        const ambientLight = new THREE.AmbientLight("#ffffff", 0.95);
        const keyLight = new THREE.DirectionalLight("#ffffff", 1.1);
        keyLight.position.set(5, 7, 5);
        const fillLight = new THREE.DirectionalLight("#8ec5ff", 0.7);
        fillLight.position.set(-4, 3, -5);

        const grid = new THREE.GridHelper(16, 16, "#8fb6d5", "#d4e0ea");
        grid.position.y = -1.6;
        scene.add(ambientLight, keyLight, fillLight, grid);

        const loader = new objLoaderModule.OBJLoader();
        const object = loader.parse(source);

        object.traverse((child: any) => {
          if ("isMesh" in child && child.isMesh) {
            const mesh = child as any;
            mesh.material = new THREE.MeshStandardMaterial({
              color: "#8eb8d8",
              metalness: 0.14,
              roughness: 0.56,
              emissive: "#0f1720",
              emissiveIntensity: 0.05
            });
            mesh.castShadow = false;
            mesh.receiveShadow = false;
          }
        });

        const bounds = new THREE.Box3().setFromObject(object);
        const size = bounds.getSize(new THREE.Vector3());
        const center = bounds.getCenter(new THREE.Vector3());
        object.position.sub(center);

        const longestSide = Math.max(size.x, size.y, size.z, 0.001);
        const modelScale = 5 / longestSide;
        object.scale.setScalar(modelScale);
        scene.add(object);

        const controlsCtor = controlsModule.OrbitControls;
        controls = new controlsCtor(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.08;
        controls.target.set(0, 0, 0);
        controls.update();

        const resize = () => {
          if (!renderer || !container) {
            return;
          }
          const width = Math.max(container.clientWidth, 10);
          const height = Math.max(container.clientHeight, 10);
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
          renderer.setSize(width, height, false);
        };

        resize();
        if (typeof ResizeObserver !== "undefined") {
          resizeObserver = new ResizeObserver(resize);
          resizeObserver.observe(container);
        } else {
          resizeHandler = resize;
          window.addEventListener("resize", resizeHandler);
        }

        const renderFrame = () => {
          if (cancelled || !renderer) {
            return;
          }
          controls?.update();
          renderer.render(scene, camera);
          animationFrameId = window.requestAnimationFrame(renderFrame);
        };

        renderFrame();
        setViewportState("ready");
      } catch {
        if (!cancelled) {
          setViewportState("error");
        }
      }
    }

    void initialize();

    return () => {
      cancelled = true;
      if (animationFrameId) {
        window.cancelAnimationFrame(animationFrameId);
      }
      resizeObserver?.disconnect();
      if (resizeHandler) {
        window.removeEventListener("resize", resizeHandler);
      }
      controls?.dispose();
      renderer?.dispose();
      if (container) {
        container.innerHTML = "";
      }
    };
  }, [artifact.url]);

  return (
    <div className="viewport-3d">
      <div className="viewport-3d__hud">
        <span className="viewport-3d__badge">三维几何</span>
        <p>左键旋转，滚轮缩放，右键平移</p>
      </div>
      <div ref={hostRef} className="viewport-3d__stage" aria-label="三维几何视图" />
      {viewportState !== "ready" && (
        <div className="viewport-3d__fallback">
          <p className="viewport-placeholder__title">
            {viewportState === "error" ? "模型加载失败" : "正在准备三维视图"}
          </p>
          <p>
            {viewportState === "fallback"
              ? "当前环境不支持 WebGL，无法显示三维视图。"
              : "正在读取几何预览模型并构建可旋转视图。"}
          </p>
        </div>
      )}
    </div>
  );
}
