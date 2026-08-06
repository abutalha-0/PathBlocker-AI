const CELL = 56;
const GAP = 10;
const STEP = CELL + GAP;

const CELL_COLOR = '#2a2a3d';
const GRID_BACKGROUND = '#1e1e2e';
const WALL_COLOR = '#e0c341';
const PLAYER_COLORS = ['#4fd8ff', '#ff6b6b'];
const HIGHLIGHT_COLOR = 'rgba(224, 195, 65, 0.25)';
const HIGHLIGHT_HOVER_COLOR = 'rgba(224, 195, 65, 0.55)';
const WALL_GHOST_LEGAL_COLOR = 'rgba(224, 195, 65, 0.55)';
const WALL_GHOST_ILLEGAL_COLOR = 'rgba(255, 90, 90, 0.55)';

function boardPixelSize(boardSize) {
    return boardSize * CELL + (boardSize - 1) * GAP;
}

function drawCells(ctx, boardSize) {
    ctx.fillStyle = GRID_BACKGROUND;
    ctx.fillRect(0, 0, boardPixelSize(boardSize), boardPixelSize(boardSize));

    ctx.fillStyle = CELL_COLOR;
    for (let row = 0; row < boardSize; row++) {
        for (let col = 0; col < boardSize; col++) {
            ctx.fillRect(col * STEP, row * STEP, CELL, CELL);
        }
    }
}

function drawHighlights(ctx, legalTargets, hoverCell) {
    for (const [row, col] of legalTargets) {
        const isHover = hoverCell && hoverCell[0] === row && hoverCell[1] === col;
        ctx.fillStyle = isHover ? HIGHLIGHT_HOVER_COLOR : HIGHLIGHT_COLOR;
        ctx.fillRect(col * STEP, row * STEP, CELL, CELL);
    }
}

function wallRect(orientation, row, col) {
    if (orientation === 'horizontal') {
        return [col * STEP, row * STEP + CELL, 2 * CELL + GAP, GAP];
    }
    return [col * STEP + CELL, row * STEP, GAP, 2 * CELL + GAP];
}

function drawWalls(ctx, state) {
    ctx.fillStyle = WALL_COLOR;
    for (const [row, col] of state.horizontal_walls) {
        ctx.fillRect(...wallRect('horizontal', row, col));
    }
    for (const [row, col] of state.vertical_walls) {
        ctx.fillRect(...wallRect('vertical', row, col));
    }
}

function drawWallGhost(ctx, hoverWall, legalWalls) {
    if (!hoverWall) {
        return;
    }
    const { orientation, position } = hoverWall;
    const isLegal = legalWalls.some(
        ([o, [r, c]]) => o === orientation && r === position[0] && c === position[1]
    );
    ctx.fillStyle = isLegal ? WALL_GHOST_LEGAL_COLOR : WALL_GHOST_ILLEGAL_COLOR;
    ctx.fillRect(...wallRect(orientation, position[0], position[1]));
}

function drawPlayers(ctx, state) {
    state.players.forEach((player, index) => {
        const [row, col] = player.position;
        const cx = col * STEP + CELL / 2;
        const cy = row * STEP + CELL / 2;
        ctx.beginPath();
        ctx.arc(cx, cy, CELL * 0.35, 0, Math.PI * 2);
        ctx.fillStyle = PLAYER_COLORS[index];
        ctx.fill();
    });
}

function renderBoard(canvas, state, legalTargets, hoverCell, legalWalls, hoverWall) {
    const size = boardPixelSize(state.board_size);
    canvas.width = size;
    canvas.height = size;

    const ctx = canvas.getContext('2d');
    drawCells(ctx, state.board_size);
    drawHighlights(ctx, legalTargets, hoverCell);
    drawWallGhost(ctx, hoverWall, legalWalls);
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
    turnIndicator.textContent = state.winner === null ? `Player ${state.turn + 1}'s turn` : '';

    const overlay = document.getElementById('game-over');
    overlay.hidden = state.winner === null;
    if (state.winner !== null) {
        document.getElementById('game-over-message').textContent = `Player ${state.winner + 1} wins!`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('board');
    const csrfToken = document.querySelector('#csrf-form [name=csrfmiddlewaretoken]').value;

    let state = JSON.parse(document.getElementById('game-state').textContent);
    let legalTargets = [];
    let legalWalls = [];
    let hoverCell = null;
    let hoverWall = null;

    const redraw = () => {
        renderBoard(canvas, state, legalTargets, hoverCell, legalWalls, hoverWall);
        updateHud(state);
    };

    async function fetchLegalMoves() {
        if (state.winner !== null) {
            legalTargets = [];
            legalWalls = [];
            return;
        }
        const response = await fetch('/api/legal-moves');
        const data = await response.json();
        legalTargets = data.targets;
        legalWalls = data.walls;
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
        await fetchLegalMoves();
        redraw();
    }

    canvas.addEventListener('mousemove', (event) => {
        if (state.winner !== null) {
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
        if (state.winner !== null) {
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
        await fetchLegalMoves();
        redraw();
    });

    redraw();
    fetchLegalMoves().then(redraw);
});
