const CELL = 56;
const GAP = 10;
const STEP = CELL + GAP;

const CELL_COLOR = '#12141f';
const CELL_BORDER_COLOR = '#1a1d2d';
const GRID_BACKGROUND = '#0a0b12';
const PLAYER_COLORS = ['#00f3ff', '#ff2a9d'];
const PLAYER_GLOWS = ['rgba(0, 243, 255, 0.8)', 'rgba(255, 42, 157, 0.8)'];
const PLAYER_DIMS = ['rgba(0, 243, 255, 0.25)', 'rgba(255, 42, 157, 0.25)'];
const HIGHLIGHT_HOVER_ALPHA = 0.55;
const WALL_GHOST_ILLEGAL_COLOR = 'rgba(255, 90, 90, 0.55)';

function boardPixelSize(boardSize) {
    return boardSize * CELL + (boardSize - 1) * GAP;
}

function drawCells(ctx, boardSize) {
    ctx.fillStyle = GRID_BACKGROUND;
    ctx.fillRect(0, 0, boardPixelSize(boardSize), boardPixelSize(boardSize));

    ctx.fillStyle = CELL_COLOR;
    ctx.strokeStyle = CELL_BORDER_COLOR;
    for (let row = 0; row < boardSize; row++) {
        for (let col = 0; col < boardSize; col++) {
            ctx.fillRect(col * STEP, row * STEP, CELL, CELL);
            ctx.strokeRect(col * STEP + 0.5, row * STEP + 0.5, CELL - 1, CELL - 1);
        }
    }
}

function drawHighlights(ctx, legalTargets, hoverCell, playerIndex) {
    for (const [row, col] of legalTargets) {
        const isHover = hoverCell && hoverCell[0] === row && hoverCell[1] === col;
        ctx.fillStyle = isHover ? PLAYER_GLOWS[playerIndex] : PLAYER_DIMS[playerIndex];
        ctx.globalAlpha = isHover ? HIGHLIGHT_HOVER_ALPHA : 1;
        ctx.fillRect(col * STEP, row * STEP, CELL, CELL);
        ctx.globalAlpha = 1;
    }
}

function wallRect(orientation, row, col) {
    if (orientation === 'horizontal') {
        return [col * STEP, row * STEP + CELL, 2 * CELL + GAP, GAP];
    }
    return [col * STEP + CELL, row * STEP, GAP, 2 * CELL + GAP];
}

function drawGlowingRect(ctx, rect, color, glowColor) {
    ctx.save();
    ctx.shadowBlur = 12;
    ctx.shadowColor = glowColor;
    ctx.fillStyle = color;
    ctx.fillRect(...rect);
    ctx.restore();
}

function drawWalls(ctx, state) {
    for (const [row, col, owner] of state.horizontal_walls) {
        drawGlowingRect(ctx, wallRect('horizontal', row, col), PLAYER_COLORS[owner], PLAYER_GLOWS[owner]);
    }
    for (const [row, col, owner] of state.vertical_walls) {
        drawGlowingRect(ctx, wallRect('vertical', row, col), PLAYER_COLORS[owner], PLAYER_GLOWS[owner]);
    }
}

function drawWallGhost(ctx, hoverWall, legalWalls, playerIndex) {
    if (!hoverWall) {
        return;
    }
    const { orientation, position } = hoverWall;
    const isLegal = legalWalls.some(
        ([o, [r, c]]) => o === orientation && r === position[0] && c === position[1]
    );
    const rect = wallRect(orientation, position[0], position[1]);
    if (isLegal) {
        drawGlowingRect(ctx, rect, PLAYER_COLORS[playerIndex], PLAYER_GLOWS[playerIndex]);
    } else {
        ctx.fillStyle = WALL_GHOST_ILLEGAL_COLOR;
        ctx.fillRect(...rect);
    }
}

function drawPlayers(ctx, state) {
    state.players.forEach((player, index) => {
        const [row, col] = player.position;
        const cx = col * STEP + CELL / 2;
        const cy = row * STEP + CELL / 2;

        ctx.save();
        ctx.shadowBlur = 18;
        ctx.shadowColor = PLAYER_COLORS[index];
        ctx.beginPath();
        ctx.arc(cx, cy, CELL * 0.3, 0, Math.PI * 2);
        ctx.fillStyle = PLAYER_COLORS[index];
        ctx.fill();
        ctx.restore();

        ctx.beginPath();
        ctx.arc(cx, cy, CELL * 0.12, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.fill();
    });
}

function renderBoard(canvas, state, legalTargets, hoverCell, legalWalls, hoverWall) {
    const size = boardPixelSize(state.board_size);
    canvas.width = size;
    canvas.height = size;

    const ctx = canvas.getContext('2d');
    drawCells(ctx, state.board_size);
    drawHighlights(ctx, legalTargets, hoverCell, state.turn);
    drawWallGhost(ctx, hoverWall, legalWalls, state.turn);
    drawWalls(ctx, state);
    drawPlayers(ctx, state);
}

function cellFromEvent(canvas, boardSize, event) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const col = Math.floor(x / STEP);
    const row = Math.floor(y / STEP);

    if (x - col * STEP > CELL || y - row * STEP > CELL) {
        return null;
    }
    if (row < 0 || row >= boardSize || col < 0 || col >= boardSize) {
        return null;
    }
    return [row, col];
}

function wallSlotFromEvent(canvas, boardSize, event) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const col = Math.floor(x / STEP);
    const row = Math.floor(y / STEP);
    const fx = x - col * STEP;
    const fy = y - row * STEP;

    const inGapX = fx > CELL;
    const inGapY = fy > CELL;
    if (inGapX === inGapY) {
        // either inside a cell (both false) or in the ambiguous
        // corner where a horizontal and vertical slot both touch
        return null;
    }

    const maxWallCoord = boardSize - 2;
    let orientation;
    let position;
    if (inGapX) {
        const r = fy < CELL / 2 ? row - 1 : row;
        orientation = 'vertical';
        position = [r, col];
    } else {
        const c = fx < CELL / 2 ? col - 1 : col;
        orientation = 'horizontal';
        position = [row, c];
    }

    const [r, c] = position;
    if (r < 0 || r > maxWallCoord || c < 0 || c > maxWallCoord) {
        return null;
    }
    return { orientation, position };
}

function updateHud(state) {
    document.querySelectorAll('.hud-player').forEach((el) => {
        const index = Number(el.dataset.player);
        el.querySelector('span').textContent = state.players[index].walls_left;
        el.classList.toggle('active', state.turn === index && state.winner === null);
    });

    const turnIndicator = document.getElementById('turn-indicator');
    turnIndicator.classList.remove('status-p1', 'status-p2');
    if (state.winner === null) {
        turnIndicator.textContent = `Player ${state.turn + 1}'s turn`;
        turnIndicator.classList.add(state.turn === 0 ? 'status-p1' : 'status-p2');
    } else {
        turnIndicator.textContent = '';
    }

    const overlay = document.getElementById('game-over');
    overlay.hidden = state.winner === null;
    if (state.winner !== null) {
        const message = document.getElementById('game-over-message');
        message.textContent = `Player ${state.winner + 1} wins!`;
        message.style.color = PLAYER_COLORS[state.winner];
        message.style.textShadow = `0 0 12px ${PLAYER_GLOWS[state.winner]}`;
    }
}

const HUMAN_PLAYER = 0;

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('board');
    const csrfToken = document.querySelector('#csrf-form [name=csrfmiddlewaretoken]').value;
    const menu = document.getElementById('menu');
    const app = document.getElementById('app');
    const difficultyRow = document.getElementById('difficulty-row');

    let state = JSON.parse(document.getElementById('game-state').textContent);
    let legalTargets = [];
    let legalWalls = [];
    let hoverCell = null;
    let hoverWall = null;
    let settings = { mode: 'ai', difficulty: 'medium' };

    const isHumanTurn = () => settings.mode === '2p' || state.turn === HUMAN_PLAYER;

    const redraw = () => {
        renderBoard(canvas, state, legalTargets, hoverCell, legalWalls, hoverWall);
        updateHud(state);
    };

    async function fetchLegalMoves() {
        if (state.winner !== null || !isHumanTurn()) {
            legalTargets = [];
            legalWalls = [];
            return;
        }
        const response = await fetch('/api/legal-moves');
        const data = await response.json();
        legalTargets = data.targets;
        legalWalls = data.walls;
    }

    async function requestAiMove() {
        document.getElementById('turn-indicator').textContent = 'AI is thinking...';
        const response = await fetch('/api/ai-move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ difficulty: settings.difficulty }),
        });
        if (!response.ok) {
            return;
        }
        const data = await response.json();
        state = data.state;
        hoverCell = null;
        hoverWall = null;
        await fetchLegalMoves();
        redraw();
    }

    async function afterStateChange() {
        await fetchLegalMoves();
        redraw();
        if (state.winner === null && settings.mode === 'ai' && state.turn !== HUMAN_PLAYER) {
            await requestAiMove();
        }
    }

    async function submitMove(url, body) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(body),
        });
        if (!response.ok) {
            return;
        }
        const data = await response.json();
        state = data.state;
        hoverCell = null;
        hoverWall = null;
        await afterStateChange();
    }

    canvas.addEventListener('mousemove', (event) => {
        if (state.winner !== null || !isHumanTurn()) {
            return;
        }
        hoverCell = cellFromEvent(canvas, state.board_size, event);
        hoverWall = hoverCell ? null : wallSlotFromEvent(canvas, state.board_size, event);
        redraw();
    });

    canvas.addEventListener('mouseleave', () => {
        hoverCell = null;
        hoverWall = null;
        redraw();
    });

    canvas.addEventListener('click', (event) => {
        if (state.winner !== null || !isHumanTurn()) {
            return;
        }

        const cell = cellFromEvent(canvas, state.board_size, event);
        if (cell) {
            const isLegal = legalTargets.some(([r, c]) => r === cell[0] && c === cell[1]);
            if (isLegal) {
                submitMove('/api/move', { target: cell });
            }
            return;
        }

        const wallSlot = wallSlotFromEvent(canvas, state.board_size, event);
        if (wallSlot) {
            const isLegal = legalWalls.some(
                ([o, [r, c]]) => o === wallSlot.orientation && r === wallSlot.position[0] && c === wallSlot.position[1]
            );
            if (isLegal) {
                submitMove('/api/wall', { orientation: wallSlot.orientation, position: wallSlot.position });
            }
        }
    });

    document.getElementById('play-again').addEventListener('click', async () => {
        const response = await fetch('/api/new-game', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
        });
        const data = await response.json();
        state = data.state;
        hoverCell = null;
        hoverWall = null;
        await afterStateChange();
    });

    document.querySelectorAll('input[name=mode]').forEach((input) => {
        input.addEventListener('change', () => {
            difficultyRow.hidden = document.querySelector('input[name=mode]:checked').value !== 'ai';
        });
    });

    document.getElementById('back-to-menu').addEventListener('click', () => {
        app.hidden = true;
        menu.hidden = false;
    });

    document.getElementById('start-game').addEventListener('click', async () => {
        settings.mode = document.querySelector('input[name=mode]:checked').value;
        settings.difficulty = document.getElementById('difficulty').value;

        const response = await fetch('/api/new-game', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
        });
        const data = await response.json();
        state = data.state;
        hoverCell = null;
        hoverWall = null;

        menu.hidden = true;
        app.hidden = false;
        redraw();
        await afterStateChange();
    });
});
