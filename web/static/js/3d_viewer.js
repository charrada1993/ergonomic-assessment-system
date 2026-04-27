import * as THREE from 'three';
import { OrbitControls } from 'https://unpkg.com/three@0.128.0/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'https://unpkg.com/three@0.128.0/examples/jsm/loaders/GLTFLoader.js';

// ─── Scene Setup ──────────────────────────────────────────────
const scene = new THREE.Scene();
scene.background = null;

const container = document.getElementById('canvas-container') || document.body;
const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
camera.position.set(0, 1.5, 4.5);
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
controls.maxDistance = 10;
controls.target.set(0, 1, 0);

window.addEventListener('resize', () => {
    const w = container.clientWidth, h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
});

// ─── Lighting ─────────────────────────────────────────────────
scene.add(new THREE.AmbientLight(0x606080, 1.0));

const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
dirLight.position.set(2, 5, 3);
dirLight.castShadow = true;
dirLight.shadow.mapSize.set(2048, 2048);
dirLight.shadow.bias = -0.0005;
scene.add(dirLight);

const fillLight = new THREE.DirectionalLight(0x9b59ff, 0.6);
fillLight.position.set(-2, 1, -2);
scene.add(fillLight);

// ─── Ground Plane ─────────────────────────────────────────────
const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(8, 8),
    new THREE.MeshStandardMaterial({ color: 0x0a0f25, roughness: 0.1, metalness: 0.6, transparent: true, opacity: 0.8 })
);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -0.05;
floor.receiveShadow = true;
scene.add(floor);

const gridHelper = new THREE.GridHelper(8, 40, 0x1a2040, 0x0d1530);
gridHelper.position.y = -0.04;
scene.add(gridHelper);

// ─── GLTF Model ───────────────────────────────────────────────
let model = null;
const bones = {};
const targetPositions = Array.from({ length: 33 }, () => new THREE.Vector3());
let lastLandmarks = null;

// ─── Bone Rotation Helper ─────────────────────────────────────
const _q = new THREE.Quaternion();
const _up = new THREE.Vector3(0, 1, 0);
const _v1 = new THREE.Vector3();

function rotateBoneToward(bone, fromPos, toPos) {
    if (!bone || !fromPos || !toPos) return;
    _v1.subVectors(toPos, fromPos);
    if (_v1.length() < 0.001) return;
    _v1.normalize();
    _q.setFromUnitVectors(_up, _v1);
    const parentWorldQuat = new THREE.Quaternion();
    if (bone.parent) bone.parent.getWorldQuaternion(parentWorldQuat);
    bone.quaternion.copy(parentWorldQuat.clone().invert().multiply(_q));
}

// ─── Load the Rigged Model ────────────────────────────────────
const loader = new GLTFLoader();
loader.load('/static/models/xbot.glb', (gltf) => {
    model = gltf.scene;

    // Mixamo/FBX models export in centimetres. Scale to metres.
    // Xbot is ~170 cm tall → at scale 0.01 → 1.7 m — perfect human height.
    const SCALE = 0.01;
    model.scale.set(SCALE, SCALE, SCALE);

    // IMPORTANT: must updateMatrixWorld after scaling before computing bbox
    model.updateMatrixWorld(true);
    const bbox = new THREE.Box3().setFromObject(model);
    model.position.y = -bbox.min.y;   // ground the feet to y=0
    model.position.x = 0;
    model.position.z = 0;

    model.traverse((child) => {
        if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
        }
        if (child.isBone || child.type === 'Bone') {
            bones[child.name] = child;
        }
    });

    scene.add(model);

    // Frame the full body
    camera.position.set(0, 1.0, 3.5);
    controls.target.set(0, 1.0, 0);
    controls.update();

    console.log('Xbot loaded. Bones:', Object.keys(bones).length);

    const statusEl = document.getElementById('viewer3dStatus');
    if (statusEl) statusEl.innerHTML = '<i class="fas fa-circle" style="color:var(--cyan);font-size:0.5rem"></i> 3D model ready — waiting for pose';

}, (xhr) => {
    const pct = xhr.total ? Math.round((xhr.loaded / xhr.total) * 100) : '...';
    const statusEl = document.getElementById('viewer3dStatus');
    if (statusEl) statusEl.innerHTML = `<i class="fas fa-circle" style="color:var(--yellow);font-size:0.5rem"></i> Loading model… ${pct}%`;

}, (err) => {
    console.error('Error loading model:', err);
    const statusEl = document.getElementById('viewer3dStatus');
    if (statusEl) statusEl.innerHTML = '<i class="fas fa-circle" style="color:var(--red);font-size:0.5rem"></i> Model load failed';
});

// ─── Apply Pose to Bones ──────────────────────────────────────
function applyPoseToBones() {
    if (!model || !lastLandmarks) return;

    const lp = (i) => targetPositions[i];

    const hipMid = lp(23).clone().add(lp(24)).multiplyScalar(0.5);
    const shoulderMid = lp(11).clone().add(lp(12)).multiplyScalar(0.5);

    rotateBoneToward(bones['mixamorig:Spine'],    hipMid, shoulderMid);
    rotateBoneToward(bones['mixamorig:Spine1'],   hipMid, shoulderMid);
    rotateBoneToward(bones['mixamorig:Spine2'],   hipMid, shoulderMid);
    rotateBoneToward(bones['mixamorig:Neck'],     shoulderMid, lp(0));
    rotateBoneToward(bones['mixamorig:LeftArm'],     lp(11), lp(13));
    rotateBoneToward(bones['mixamorig:LeftForeArm'], lp(13), lp(15));
    rotateBoneToward(bones['mixamorig:RightArm'],     lp(12), lp(14));
    rotateBoneToward(bones['mixamorig:RightForeArm'], lp(14), lp(16));
    rotateBoneToward(bones['mixamorig:LeftUpLeg'],  lp(23), lp(25));
    rotateBoneToward(bones['mixamorig:LeftLeg'],    lp(25), lp(27));
    rotateBoneToward(bones['mixamorig:RightUpLeg'], lp(24), lp(26));
    rotateBoneToward(bones['mixamorig:RightLeg'],   lp(26), lp(28));
}

// ─── Update Skeleton (called on socket event) ─────────────────
function updateSkeleton(landmarks) {
    if (!landmarks) return;
    lastLandmarks = landmarks;
    for (let i = 0; i < 33; i++) {
        if (landmarks[i]) {
            targetPositions[i].set(
                (landmarks[i][0] - 0.5) * 2,
                (-landmarks[i][1] + 1) * 2,
                landmarks[i][2] * 2
            );
        }
    }
}

// ─── UI & Socket.IO ───────────────────────────────────────────
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
let fpsCount = 0;
setInterval(() => { setText('viewer-fps', fpsCount); fpsCount = 0; }, 1000);

const socket = io();
socket.on('skeleton_3d', (data) => {
    if (data.landmarks) {
        updateSkeleton(data.landmarks);
        fpsCount++;
        setText('viewer-joints', data.landmarks.length);
        if (model) {
            const statusEl = document.getElementById('viewer3dStatus');
            if (statusEl) statusEl.innerHTML = '<i class="fas fa-circle" style="color:var(--green);font-size:0.5rem"></i> Receiving pose data';
        }
    }
});

// ─── Animate ──────────────────────────────────────────────────
function animate() {
    requestAnimationFrame(animate);
    controls.update();

    // Smooth lerp
    if (lastLandmarks) {
        for (let i = 0; i < 33; i++) {
            if (lastLandmarks[i]) {
                targetPositions[i].lerp(
                    new THREE.Vector3(
                        (lastLandmarks[i][0] - 0.5) * 2,
                        (-lastLandmarks[i][1] + 1) * 2,
                        lastLandmarks[i][2] * 2
                    ), 0.25
                );
            }
        }
        applyPoseToBones();
    }

    renderer.render(scene, camera);
}

animate();