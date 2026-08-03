const CELL = 56;
const GAP = 10;
const STEP = CELL + GAP;

const CELL_COLOR = '#2a2a3d';
const GRID_BACKGROUND = '#1e1e2e';
const WALL_COLOR = '#e0c341';
const PLAYER_COLORS = ['#4fd8ff', '#ff6b6b'];

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

function renderBoard(canvas, state) {
    const size = boardPixelSize(state.board_size);
    canvas.width = size;
    canvas.height = size;

    const ctx = canvas.getContext('2d');
    drawCells(ctx, state.board_size);
    drawWalls(ctx, state);
    drawPlayers(ctx, state);
}

document.addEventListener('DOMContentLoaded', () => {
    const state = JSON.parse(document.getElementById('game-state').textContent);
    const canvas = document.getElementById('board');
    renderBoard(canvas, state);
});
