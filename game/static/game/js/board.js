const CELL = 56;
const GAP = 10;
const STEP = CELL + GAP;

const CELL_COLOR = '#2a2a3d';
const GRID_BACKGROUND = '#1e1e2e';
const WALL_COLOR = '#e0c341';
const PLAYER_COLORS = ['#4fd8ff', '#ff6b6b'];
const HIGHLIGHT_COLOR = 'rgba(224, 195, 65, 0.25)';
const HIGHLIGHT_HOVER_COLOR = 'rgba(224, 195, 65, 0.55)';

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

function drawWalls(ctx, state) {
    ctx.fillStyle = WALL_COLOR;
    for (const [row, col] of state.horizontal_walls) {
        ctx.fillRect(col * STEP, row * STEP + CELL, 2 * CELL + GAP, GAP);
    }
    for (const [row, col] of state.vertical_walls) {
        ctx.fillRect(col * STEP + CELL, row * STEP, GAP, 2 * CELL + GAP);
    }
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

function renderBoard(canvas, state, legalTargets, hoverCell) {
    const size = boardPixelSize(state.board_size);
    canvas.width = size;
    canvas.height = size;

    const ctx = canvas.getContext('2d');
    drawCells(ctx, state.board_size);
    drawHighlights(ctx, legalTargets, hoverCell);
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

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('board');
    const csrfToken = document.querySelector('#csrf-form [name=csrfmiddlewaretoken]').value;

    let state = JSON.parse(document.getElementById('game-state').textContent);
    let legalTargets = [];
    let hoverCell = null;

    const redraw = () => renderBoard(canvas, state, legalTargets, hoverCell);

    async function fetchLegalMoves() {
        const response = await fetch('/api/legal-moves');
        const data = await response.json();
        legalTargets = data.targets;
    }

    async function movePawn(target) {
        const response = await fetch('/api/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ target }),
        });
        if (!response.ok) {
            return;
        }
        const data = await response.json();
        state = data.state;
        await fetchLegalMoves();
        redraw();
        if (data.winner !== null) {
            alert(`Player ${data.winner + 1} wins!`);
        }
    }

    canvas.addEventListener('mousemove', (event) => {
        hoverCell = cellFromEvent(canvas, state.board_size, event);
        redraw();
    });

    canvas.addEventListener('mouseleave', () => {
        hoverCell = null;
        redraw();
    });

    canvas.addEventListener('click', (event) => {
        const cell = cellFromEvent(canvas, state.board_size, event);
        if (!cell) {
            return;
        }
        const isLegal = legalTargets.some(([r, c]) => r === cell[0] && c === cell[1]);
        if (isLegal) {
            movePawn(cell);
        }
    });

    redraw();
    fetchLegalMoves().then(redraw);
});
