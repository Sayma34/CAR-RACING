(() => {
    "use strict";

    const canvas = document.getElementById("game");
    const ctx = canvas.getContext("2d");
    const W = canvas.width;
    const H = canvas.height;
    const speedSettings = {
        normal: { start: 1, max: 8 },
        medium: { start: 3, max: 15 },
        hard: { start: 5, max: 22 }
    };
    const road = { left: 150, right: 450 };
    const lanes = [200, 300, 400];
    const state = {
        mode: "start", playerX: 300, distance: 0, score: 0, lives: 3,
        speedMode: "normal", speed: 1, maxSpeed: 8, spawnTimer: 0, shake: 0, entities: [],
        keys: {}, shield: 0, nitro: 0, magnet: 0, police: false, hitCount: 0,
        lastTime: 0, roadOffset: 0
    };
    const el = id => document.getElementById(id);

    function reset() {
        const selectedSpeed = speedSettings[state.speedMode];
        state.mode = "playing"; state.playerX = 300; state.distance = 0; state.score = 0;
        state.lives = 3; state.speed = selectedSpeed.start; state.maxSpeed = selectedSpeed.max; state.spawnTimer = 0; state.shake = 0;
        state.entities = []; state.shield = 0; state.nitro = 0; state.magnet = 0; state.police = false; state.hitCount = 0;
        el("overlay").classList.add("hidden");
    }

    function startOrPause() {
        if (state.mode === "start" || state.mode === "gameover") reset();
        else if (state.mode === "playing") pause();
        else { state.mode = "playing"; el("overlay").classList.add("hidden"); }
    }

    function pause() {
        if (state.mode !== "playing") return;
        state.mode = "paused";
        showOverlay("Paused", "Take a breath. Your run is waiting.", "Resume race");
    }

    function showOverlay(title, copy, button) {
        el("overlay-title").textContent = title;
        el("overlay-copy").textContent = copy;
        el("start-button").textContent = button;
        el("overlay").classList.remove("hidden");
    }

    function chooseSpeed(mode) {
        state.speedMode = mode;
        const selectedSpeed = speedSettings[mode];
        if (state.mode === "start" || state.mode === "gameover") {
            state.speed = selectedSpeed.start;
            state.maxSpeed = selectedSpeed.max;
        }
        document.querySelectorAll(".speed-choice").forEach(button => button.classList.toggle("active", button.dataset.speed === mode));
    }

    function spawn() {
        const roll = Math.random();
        const x = lanes[Math.floor(Math.random() * lanes.length)];
        let type = roll < .42 ? "barrel" : roll < .78 ? "car" : roll < .88 ? "coin" : ["shield", "nitro", "magnet"][Math.floor(Math.random() * 3)];
        state.entities.push({ type, x, y: -80, w: type === "car" ? 42 : 30, h: type === "car" ? 62 : 30, color: ["#f26c58", "#63c9d8", "#e9c84a"][Math.floor(Math.random() * 3)], drift: type === "car" ? (Math.random() - .5) * 1.2 : 0 });
    }

    function update(dt) {
        if (state.mode !== "playing") return;
        const frame = dt / 16.67;
        const weatherIndex = Math.floor(state.distance / 3000) % 3;
        const friction = weatherIndex === 1 ? .82 : .9;
        if (state.keys.a || state.keys.ArrowLeft) state.playerX -= (weatherIndex === 1 ? 4 : 2.7) * frame;
        if (state.keys.d || state.keys.ArrowRight) state.playerX += (weatherIndex === 1 ? 4 : 2.7) * frame;
        state.playerX = Math.max(road.left + 25, Math.min(road.right - 25, state.playerX));
        state.speed = Math.min(state.maxSpeed, state.speed + .0015 * frame);
        const actualSpeed = state.speed * (state.nitro > 0 ? 2 : 1);
        state.distance += actualSpeed * frame; state.score = Math.floor(state.distance / 100);
        state.roadOffset = (state.roadOffset + actualSpeed * frame) % 100;
        state.spawnTimer -= actualSpeed * frame;
        if (state.spawnTimer <= 0) { spawn(); state.spawnTimer = Math.max(150, 400 - state.distance / 100); }
        state.shield = Math.max(0, state.shield - dt); state.nitro = Math.max(0, state.nitro - dt); state.magnet = Math.max(0, state.magnet - dt); state.shake = Math.max(0, state.shake - dt);
        for (const item of state.entities) {
            item.y += actualSpeed * frame + (item.type === "car" ? 1.5 : 0);
            item.x += item.drift * frame;
            if (state.magnet > 0 && item.type === "coin" && Math.abs(item.x - state.playerX) < 200) item.x += Math.sign(state.playerX - item.x) * 4 * frame;
        }
        const player = { x: state.playerX, y: H - 145, w: 40, h: 60 };
        for (const item of state.entities) {
            if (item.taken || !collides(player, item)) continue;
            item.taken = true;
            if (item.type === "coin") state.distance += 500;
            else if (item.type === "shield") state.shield = 8000;
            else if (item.type === "nitro") state.nitro = 5000;
            else if (item.type === "magnet") state.magnet = 7000;
            else if (state.shield > 0) state.shield = 0;
            else { state.lives--; state.hitCount++; if (state.hitCount >= 3) state.police = true; state.shake = 300; if (state.lives <= 0) { state.mode = "gameover"; showOverlay("Run over", `You scored ${state.score} points.`, "Race again"); } }
        }
        state.entities = state.entities.filter(item => !item.taken && item.y < H + 100);
        updateHud(weatherIndex);
    }

    function collides(a, b) { return Math.abs(a.x - b.x) < (a.w + b.w) / 2 && Math.abs(a.y - b.y) < (a.h + b.h) / 2; }

    function updateHud(weatherIndex) {
        const biomeIndex = Math.floor(state.score / 1000) % 3;
        el("score").textContent = state.score; el("distance").textContent = Math.floor(state.distance); el("lives").textContent = state.lives; el("speed").textContent = Math.floor(state.speed);
        el("biome").textContent = ["Forest", "Desert", "City"][biomeIndex]; el("weather").textContent = ["Clear", "Rain", "Snow"][weatherIndex]; el("police").textContent = state.police ? "Active" : "Inactive";
        el("shield").textContent = state.shield > 0 ? `${Math.ceil(state.shield / 1000)}s` : "READY"; el("nitro").textContent = state.nitro > 0 ? "ACTIVE" : "READY"; el("magnet").textContent = state.magnet > 0 ? "ACTIVE" : "READY";
        el("status").textContent = state.mode.toUpperCase();
    }

    function draw() {
        const biome = Math.floor(state.score / 1000) % 3;
        const weather = Math.floor(state.distance / 3000) % 3;
        const shake = state.shake > 0 ? (Math.random() - .5) * 7 : 0;
        ctx.save(); ctx.translate(shake, shake);
        ctx.fillStyle = ["#9db391", "#d5b879", "#303c50"][biome]; ctx.fillRect(0, 0, W, H);
        ctx.fillStyle = ["#2c3435", "#514e45", "#202631"][biome]; ctx.fillRect(road.left, 0, road.right - road.left, H);
        ctx.fillStyle = "#e5e2d4"; ctx.fillRect(road.left, 0, 5, H); ctx.fillRect(road.right - 5, 0, 5, H);
        ctx.fillStyle = biome === 2 ? "#7a8491" : "#dad8c9";
        for (let y = -100 + state.roadOffset; y < H; y += 100) { ctx.fillRect(248, y, 5, 42); ctx.fillRect(348, y, 5, 42); }
        for (const item of state.entities) drawEntity(item);
        drawCar(state.playerX, H - 145, 40, 60, "#e83e52");
        if (state.shield > 0) { ctx.strokeStyle = "#62d8ef"; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(state.playerX, H - 145, 39, 0, Math.PI * 2); ctx.stroke(); }
        if (weather === 1) drawRain(); if (weather === 2) drawSnow();
        if (state.police && Math.floor(performance.now() / 350) % 2 === 0) { ctx.fillStyle = "#ff5c51"; ctx.font = "700 18px Space Mono"; ctx.textAlign = "center"; ctx.fillText("POLICE PURSUIT", W / 2, 48); }
        ctx.restore();
        requestAnimationFrame(loop);
    }

    function drawEntity(item) {
        if (item.type === "car") drawCar(item.x, item.y, item.w, item.h, item.color);
        else if (item.type === "barrel") { ctx.fillStyle = "#873d3b"; ctx.fillRect(item.x - 16, item.y - 16, 32, 32); ctx.strokeStyle = "#d8b7a0"; ctx.strokeRect(item.x - 16, item.y - 5, 32, 10); }
        else { const colors = { coin: "#f2ca47", shield: "#55c5e4", nitro: "#ef6c52", magnet: "#e45b68" }; ctx.fillStyle = colors[item.type]; ctx.beginPath(); ctx.arc(item.x, item.y, 15, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = "#fff4bb"; ctx.font = "bold 12px Space Mono"; ctx.textAlign = "center"; ctx.fillText(item.type === "coin" ? "$" : item.type[0].toUpperCase(), item.x, item.y + 4); }
    }

    function drawCar(x, y, w, h, color) { ctx.fillStyle = "#151c1e"; ctx.fillRect(x - w / 2 - 5, y - h / 2 + 8, 7, 18); ctx.fillRect(x + w / 2 - 2, y - h / 2 + 8, 7, 18); ctx.fillRect(x - w / 2 - 5, y + h / 2 - 26, 7, 18); ctx.fillRect(x + w / 2 - 2, y + h / 2 - 26, 7, 18); ctx.fillStyle = color; ctx.fillRect(x - w / 2, y - h / 2, w, h); ctx.fillStyle = "#bfe7e4"; ctx.fillRect(x - w / 2 + 6, y - h / 2 + 9, w - 12, 19); ctx.fillStyle = "#f8df58"; ctx.fillRect(x - w / 2 + 5, y - h / 2 + 3, 8, 5); ctx.fillRect(x + w / 2 - 13, y - h / 2 + 3, 8, 5); ctx.fillStyle = "#ff5c51"; ctx.fillRect(x - w / 2 + 6, y + h / 2 - 7, 8, 4); ctx.fillRect(x + w / 2 - 14, y + h / 2 - 7, 8, 4); }
    function drawRain() { ctx.strokeStyle = "rgba(190,220,255,.55)"; ctx.lineWidth = 2; for (let i = 0; i < 55; i++) { const x = (i * 83 + state.distance * 2) % W; const y = (i * 47 + state.distance * 4) % H; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 7, y + 23); ctx.stroke(); } }
    function drawSnow() { ctx.fillStyle = "rgba(255,255,255,.8)"; for (let i = 0; i < 65; i++) { const x = (i * 61 + Math.sin(state.distance / 200 + i) * 20) % W; const y = (i * 43 + state.distance) % H; ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.fill(); } }

    function loop(time) { const dt = Math.min(40, time - state.lastTime || 16); state.lastTime = time; update(dt); draw(); }
    document.addEventListener("keydown", event => { state.keys[event.key] = true; if (event.key.toLowerCase() === "p") startOrPause(); if (["ArrowLeft", "ArrowRight", "a", "d", " "].includes(event.key)) event.preventDefault(); });
    document.addEventListener("keyup", event => { state.keys[event.key] = false; });
    document.querySelectorAll(".speed-choice").forEach(button => button.addEventListener("click", () => chooseSpeed(button.dataset.speed)));
    el("start-button").addEventListener("click", startOrPause); el("pause-button").addEventListener("click", () => state.mode === "playing" ? pause() : startOrPause());
    updateHud(0); requestAnimationFrame(loop);
})();