import * as THREE from 'three';
import { OrbitControls } from 'https://unpkg.com/three@0.128.0/examples/jsm/controls/OrbitControls.js';

// ─── Scene Setup ──────────────────────────────────────────────
const scene = new THREE.Scene();
scene.background = null;

const container = document.getElementById('canvas-container') || document.body;
const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
camera.position.set(0, 1.5, 3.5);
camera.lookAt(0, 1, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
container.appendChild(renderer.domElement);

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

const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
dirLight.position.set(2, 5, 3);
dirLight.castShadow = true;
dirLight.shadow.mapSize.width = 2048;
dirLight.shadow.mapSize.height = 2048;
dirLight.shadow.bias = -0.0005;
scene.add(dirLight);

const fillLight = new THREE.DirectionalLight(0x9b59ff, 0.6);
fillLight.position.set(-2, 1, -2);
scene.add(fillLight);

// ─── Ground Plane ─────────────────────────────────────────────
const floorGeometry = new THREE.PlaneGeometry(8, 8);
const floorMaterial = new THREE.MeshStandardMaterial({
    color: 0x0a0f25,
    roughness: 0.1,
    metalness: 0.6,
    transparent: true,
    opacity: 0.8
});
const floor = new THREE.Mesh(floorGeometry, floorMaterial);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -0.1;
floor.receiveShadow = true;
scene.add(floor);

const gridHelper = new THREE.GridHelper(8, 40, 0x1a2040, 0x0d1530);
gridHelper.position.y = -0.09;
scene.add(gridHelper);

// ─── Anatomical Procedural Skeleton ───────────────────────────
const connections = [
    [11,13], [13,15], // Left Arm
    [12,14], [14,16], // Right Arm
    [11,12], [11,23], [12,24], [23,24], // Torso
    [23,25], [25,27], // Left Leg
    [24,26], [26,28], // Right Leg
    [0,11], [0,12], // Neck to shoulders
];

const joints = [];
const targetSpheres = [];
const bones = [];

// Shared anatomical bone material (bone white)
const boneMat = new THREE.MeshStandardMaterial({ 
    color: 0xe0e5ec, 
    roughness: 0.7, 
    metalness: 0.1 
});
// Shared joint material (slightly darker/bluish cartilage)
const jointMat = new THREE.MeshStandardMaterial({ 
    color: 0x8ba4b5, 
    roughness: 0.4, 
    metalness: 0.2 
});

// Tapered bone geometry (thicker at top, thinner at bottom)
const boneGeometry = new THREE.CylinderGeometry(0.02, 0.012, 1, 12);
boneGeometry.translate(0, 0.5, 0);
boneGeometry.rotateX(Math.PI / 2);

function createAnatomicalSkeleton() {
    for (let i = 0; i < 33; i++) {
        let geo;
        if (i === 0) {
            // Skull: an ellipsoid
            geo = new THREE.SphereGeometry(0.08, 24, 24);
            geo.scale(1, 1.3, 1.1); // Make it skull shaped
        } else {
            // Normal joints
            geo = new THREE.SphereGeometry(0.025, 16, 16);
        }

        const mesh = new THREE.Mesh(geo, i === 0 ? boneMat : jointMat);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.visible = false;
        scene.add(mesh);
        joints.push(mesh);
        targetSpheres.push(new THREE.Vector3());
    }

    for (let i = 0; i < connections.length; i++) {
        // Use a thicker geometry for the torso to simulate ribcage mass
        const isTorso = (i >= 4 && i <= 7);
        let geo = boneGeometry;
        if (isTorso) {
            geo = new THREE.CylinderGeometry(0.03, 0.03, 1, 12);
            geo.translate(0, 0.5, 0);
            geo.rotateX(Math.PI / 2);
        }

        const cylinder = new THREE.Mesh(geo, boneMat);
        cylinder.castShadow = true;
        cylinder.receiveShadow = true;
        cylinder.visible = false;
        scene.add(cylinder);
        bones.push(cylinder);
    }
}
createAnatomicalSkeleton();

// ─── Update Logic ─────────────────────────────────────────────
function updateSkeleton(landmarks) {
    if (!landmarks) return;
    
    // Update target positions
    for (let i = 0; i < 33; i++) {
        if (landmarks[i] && targetSpheres[i]) {
            targetSpheres[i].set(
                (landmarks[i][0] - 0.5) * 2,
                (-landmarks[i][1] + 1) * 2,
                landmarks[i][2] * 2
            );
            if (!joints[i].visible) {
                joints[i].position.copy(targetSpheres[i]);
                joints[i].visible = true;
            }
        }
    }
}

// ─── UI Helpers & Socket.IO ───────────────────────────────────
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
let fpsCount = 0;
setInterval(() => { setText('viewer-fps', fpsCount); fpsCount = 0; }, 1000);

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

// ─── Animate ──────────────────────────────────────────────────
function animate() {
    requestAnimationFrame(animate);
    controls.update();

    const lerpFactor = 0.3;
    
    // Animate joints
    for (let i = 0; i < 33; i++) {
        if (joints[i].visible) {
            joints[i].position.lerp(targetSpheres[i], lerpFactor);
        }
    }
    
    // Animate bones
    for (let i = 0; i < connections.length; i++) {
        const [a, b] = connections[i];
        if (joints[a].visible && joints[b].visible) {
            const start = joints[a].position;
            const end = joints[b].position;
            const distance = start.distanceTo(end);
            bones[i].position.copy(start);
            bones[i].lookAt(end);
            bones[i].scale.set(1, 1, distance);
            bones[i].visible = true;
        }
    }

    renderer.render(scene, camera);
}

animate();