import * as THREE from 'three';
import { OrbitControls } from 'https://unpkg.com/three@0.128.0/examples/jsm/controls/OrbitControls.js';

// ─── Scene Setup ──────────────────────────────────────────────
const scene = new THREE.Scene();
scene.background = null; // Transparent — glassmorphic background shows through

const container = document.getElementById('canvas-container') || document.body;
const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
camera.position.set(0, 1.5, 3.5);
camera.lookAt(0, 1, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

// Orbit controls with smooth damping
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 1.5;
controls.maxDistance = 8;
controls.target.set(0, 1, 0);

window.addEventListener('resize', () => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
});

// ─── Lighting ─────────────────────────────────────────────────
const ambientLight = new THREE.AmbientLight(0x404060, 0.8);
scene.add(ambientLight);
const dirLight = new THREE.DirectionalLight(0x00d4ff, 1.2);
dirLight.position.set(2, 4, 2);
scene.add(dirLight);
const fillLight = new THREE.DirectionalLight(0x9b59ff, 0.4);
fillLight.position.set(-2, 1, -2);
scene.add(fillLight);

// ─── Grid Helper ──────────────────────────────────────────────
const gridHelper = new THREE.GridHelper(4, 20, 0x1a2040, 0x0d1530);
scene.add(gridHelper);

// ─── Skeleton Definition ──────────────────────────────────────
const connections = [
    // Arms
    [11,13], [13,15],
    [12,14], [14,16],
    // Torso
    [11,12], [11,23], [12,24], [23,24],
    // Legs
    [23,25], [25,27], [24,26], [26,28],
    // Neck (head to shoulders midpoint approximation)
    [0,11], [0,12],
];

// Joint colour groups
const JOINT_COLORS = {
    head: 0x00d4ff,
    upper: 0x00e5a0,
    lower: 0xffc94d,
    hip:   0x9b59ff,
    leg:   0xff7c3e,
};
function getJointColor(idx) {
    if (idx === 0) return JOINT_COLORS.head;
    if (idx <= 10) return JOINT_COLORS.head;
    if (idx <= 16) return JOINT_COLORS.upper;
    if (idx <= 22) return JOINT_COLORS.lower;
    if (idx <= 24) return JOINT_COLORS.hip;
    return JOINT_COLORS.leg;
}
function getBoneColor(a, b) {
    if (a <= 1 || b <= 1) return 0x00d4ff;
    if (a <= 16 && b <= 16) return 0x00e5a0;
    if (a >= 23 || b >= 23) return 0xff7c3e;
    return 0xffc94d;
}

const spheres = [];
const lines = [];

function createSkeleton() {
    for (let i = 0; i < 33; i++) {
        const sphere = new THREE.Mesh(
            new THREE.SphereGeometry(0.025, 12, 12),
            new THREE.MeshStandardMaterial({
                color: getJointColor(i),
                emissive: getJointColor(i),
                emissiveIntensity: 0.3,
                roughness: 0.3,
                metalness: 0.5,
            })
        );
        sphere.visible = false;
        scene.add(sphere);
        spheres.push(sphere);
    }
    for (let i = 0; i < connections.length; i++) {
        const [a, b] = connections[i];
        const mat = new THREE.LineBasicMaterial({
            color: getBoneColor(a, b),
            linewidth: 2,
        });
        const geo = new THREE.BufferGeometry();
        const line = new THREE.Line(geo, mat);
        line.visible = false;
        scene.add(line);
        lines.push(line);
    }
}

function updateSkeleton(landmarks) {
    if (!landmarks) return;
    for (let i = 0; i < 33; i++) {
        if (landmarks[i] && spheres[i]) {
            spheres[i].position.set(
                (landmarks[i][0] - 0.5) * 2,
                (-landmarks[i][1] + 1) * 2,
                landmarks[i][2] * 2
            );
            spheres[i].visible = true;
        }
    }
    for (let i = 0; i < connections.length; i++) {
        const [a, b] = connections[i];
        if (landmarks[a] && landmarks[b]) {
            const pts = [
                new THREE.Vector3((landmarks[a][0]-0.5)*2, (-landmarks[a][1]+1)*2, landmarks[a][2]*2),
                new THREE.Vector3((landmarks[b][0]-0.5)*2, (-landmarks[b][1]+1)*2, landmarks[b][2]*2),
            ];
            const geo = new THREE.BufferGeometry().setFromPoints(pts);
            lines[i].geometry.dispose();
            lines[i].geometry = geo;
            lines[i].visible = true;
        }
    }
}

// ─── UI Helpers ───────────────────────────────────────────────
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
let fpsCount = 0;
setInterval(() => { setText('viewer-fps', fpsCount); fpsCount = 0; }, 1000);

// ─── Socket.IO ────────────────────────────────────────────────
const socket = io();

socket.on('skeleton_3d', (data) => {
    if (data.landmarks) {
        updateSkeleton(data.landmarks);
        fpsCount++;
        setText('viewer-joints', data.landmarks.length);
        const statusEl = document.getElementById('viewer3dStatus');
        if (statusEl) statusEl.innerHTML = '<i class="fas fa-circle" style="color:var(--green);font-size:0.5rem"></i> Receiving pose data';
    }
});

socket.on('config', (cfg) => {
    const modeMap = { 1: 'Single-view', 2: 'Dual-view', 3: 'Multi-view 3D' };
    setText('viewer-cam-mode', modeMap[cfg.mode] || 'Unknown');
});

// ─── Animate ──────────────────────────────────────────────────
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

createSkeleton();
animate();