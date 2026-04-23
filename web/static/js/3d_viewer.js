import * as THREE from 'three';
import { OrbitControls } from 'https://unpkg.com/three@0.128.0/examples/jsm/controls/OrbitControls.js';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111122);
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(2, 1.5, 3);
camera.lookAt(0, 1, 0);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);
new OrbitControls(camera, renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0x404040);
scene.add(ambientLight);
const dirLight = new THREE.DirectionalLight(0xffffff, 1);
dirLight.position.set(1, 2, 1);
scene.add(dirLight);

// Helper: axes grid
const gridHelper = new THREE.GridHelper(5, 20, 0x888888, 0x444444);
scene.add(gridHelper);

// Skeleton objects
const spheres = [];
const lines = [];

// Define skeleton connections (MediaPipe indices)
const connections = [
    [11,13], [13,15], [12,14], [14,16],  // arms
    [11,23], [12,24],                     // torso to hips
    [23,25], [25,27], [24,26], [26,28],   // legs
    [11,12], [23,24]                      // shoulders and hips cross
];

function createSkeleton() {
    // Spheres for joints
    for (let i = 0; i < 33; i++) {
        const sphere = new THREE.Mesh(
            new THREE.SphereGeometry(0.03, 16, 16),
            new THREE.MeshStandardMaterial({ color: 0x00aaff })
        );
        scene.add(sphere);
        spheres.push(sphere);
    }
    // Lines for bones
    for (let i = 0; i < connections.length; i++) {
        const material = new THREE.LineBasicMaterial({ color: 0xffaa44 });
        const geometry = new THREE.BufferGeometry();
        const line = new THREE.Line(geometry, material);
        scene.add(line);
        lines.push(line);
    }
}

function updateSkeleton(landmarks) {
    if (!landmarks) return;
    for (let i = 0; i < 33; i++) {
        if (landmarks[i] && spheres[i]) {
            spheres[i].position.set(landmarks[i][0] - 0.5, -landmarks[i][1] + 1, landmarks[i][2]);
        }
    }
    for (let i = 0; i < connections.length; i++) {
        const [a, b] = connections[i];
        if (landmarks[a] && landmarks[b]) {
            const points = [
                new THREE.Vector3(landmarks[a][0]-0.5, -landmarks[a][1]+1, landmarks[a][2]),
                new THREE.Vector3(landmarks[b][0]-0.5, -landmarks[b][1]+1, landmarks[b][2])
            ];
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            lines[i].geometry.dispose();
            lines[i].geometry = geometry;
        }
    }
}

// Socket.IO connection to receive skeleton
const socket = io();
socket.on('skeleton_3d', (data) => {
    if (data.landmarks) {
        updateSkeleton(data.landmarks);
    }
});

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
createSkeleton();
animate();