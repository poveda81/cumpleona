export function createPuzzleManager(dom) {
  let current = null;

  const closeModal = () => {
    dom.modal.classList.remove("is-open");
    dom.modal.setAttribute("aria-hidden", "true");
  };

  const openModal = () => {
    dom.modal.classList.add("is-open");
    dom.modal.setAttribute("aria-hidden", "false");
  };

  const hide = () => {
    closeModal();
    dom.content.innerHTML = "";
    dom.message.textContent = "";
    dom.title.textContent = "";
    dom.hint.textContent = "";
    dom.description.textContent = "";
    dom.continueBtn.style.display = "none";
    current = null;
  };

  const renderSorting = (mergedConfig, onSuccess) => {
    const items = [...(mergedConfig.data?.items || [])];
    const correctOrder = mergedConfig.data?.correctOrder || [];
    current = {
      type: "sorting",
      selected: [],
      correctOrder,
      mergedConfig
    };

    const renderLists = () => {
      dom.content.innerHTML = "";
      const availableBox = document.createElement("div");
      availableBox.style.flex = "1";
      const availableLabel = document.createElement("div");
      availableLabel.className = "puzzle-badge";
      availableLabel.textContent = "Tarjetas disponibles";
      availableBox.appendChild(availableLabel);

      const selectedBox = document.createElement("div");
      selectedBox.style.flex = "1";
      const selectedLabel = document.createElement("div");
      selectedLabel.className = "puzzle-badge";
      selectedLabel.textContent = "Orden elegido";
      selectedBox.appendChild(selectedLabel);

      const availableList = document.createElement("div");
      availableList.style.display = "flex";
      availableList.style.flexWrap = "wrap";
      availableList.style.gap = "6px";

      items.forEach(item => {
        const btn = document.createElement("button");
        btn.className =
          "puzzle-token" + (current.selected.includes(item) ? " disabled" : "");
        btn.textContent = item;
        btn.disabled = current.selected.includes(item);
        btn.addEventListener("click", () => {
          if (current.selected.includes(item)) return;
          current.selected.push(item);
          renderLists();
        });
        availableList.appendChild(btn);
      });

      const selectedList = document.createElement("div");
      selectedList.style.display = "flex";
      selectedList.style.flexWrap = "wrap";
      selectedList.style.gap = "6px";

      current.selected.forEach((item, idx) => {
        const btn = document.createElement("button");
        btn.className = "puzzle-token";
        btn.textContent = `${idx + 1}. ${item}`;
        btn.addEventListener("click", () => {
          current.selected.splice(idx, 1);
          renderLists();
        });
        selectedList.appendChild(btn);
      });

      availableBox.appendChild(availableList);
      selectedBox.appendChild(selectedList);
      dom.content.appendChild(availableBox);
      dom.content.appendChild(selectedBox);
    };

    const failMessage =
      mergedConfig.failText ||
      "El orden no parece correcto. Revisa la pista y vuelve a intentarlo.";

    const onCheck = () => {
      const sel = current.selected;
      if (sel.length !== correctOrder.length) {
        dom.message.textContent = "Aún faltan tarjetas por colocar.";
        dom.message.style.color = "#ffb3b3";
        return;
      }
      const ok = sel.every((val, idx) => val === correctOrder[idx]);
      if (ok) {
        current.solved = true;
        const code = mergedConfig.data?.code ? ` Código: ${mergedConfig.data.code}` : "";
        dom.message.textContent = "¡Orden correcto!" + code;
        dom.message.style.color = "#3cff3c";
        if (mergedConfig.successNext) {
          dom.continueBtn.style.display = "inline-flex";
        }
        if (mergedConfig.onSolve) mergedConfig.onSolve(sel);
        if (onSuccess && mergedConfig.successNext) {
          dom.continueBtn.onclick = () => onSuccess(mergedConfig.successNext);
        }
      } else {
        dom.message.textContent = failMessage;
        dom.message.style.color = "#ffb3b3";
      }
    };

    const onReset = () => {
      current.selected = [];
      current.solved = false;
      dom.continueBtn.style.display = "none";
      dom.message.textContent = "";
      renderLists();
    };

    dom.checkBtn.onclick = onCheck;
    dom.resetBtn.onclick = onReset;
    dom.continueBtn.style.display = "none";
    renderLists();
  };

  const renderPattern = (mergedConfig, onSuccess) => {
    const sequence = mergedConfig.data?.sequence || [];
    const maxAttempts = mergedConfig.data?.maxAttempts || 3;
    let attempt = 0;
    let currentInput = [];

    dom.content.innerHTML = "";
    const colors = mergedConfig.data?.colors || {
      rojo: "#ffde59",
      verde: "#ff6b6b",
      azul: "#6bff6b",
      amarillo: "#6bb5ff"
    };

    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const tones = {
      rojo: 660,
      verde: 440,
      azul: 520,
      amarillo: 360
    };

    const playTone = (freq, duration = 0.25) => {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      const now = audioCtx.currentTime;
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(0.2, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
      osc.start(now);
      osc.stop(now + duration);
    };

    const grid = document.createElement("div");
    grid.className = "puzzle-pattern-grid";
    const options = Array.from(new Set(sequence));
    let playingBack = false;
    const buttonsMap = new Map();

    const renderDots = () => {
      const wrap = document.createElement("div");
      wrap.className = "pattern-dots";
      currentInput.forEach(key => {
        const dot = document.createElement("span");
        dot.className = "pattern-dot";
        dot.style.background = colors[key] || "#fff";
        wrap.appendChild(dot);
      });
      dom.message.innerHTML = "";
      dom.message.appendChild(wrap);
    };

    options.forEach(opt => {
      const btn = document.createElement("button");
      btn.className = "puzzle-pattern-btn";
      btn.style.background = colors[opt] || "#fff";
      btn.dataset.key = opt;
      btn.textContent = opt.toUpperCase();
      btn.setAttribute("aria-label", opt.toUpperCase());
      btn.addEventListener("click", () => {
        if (playingBack) return;
        currentInput.push(opt);
        renderDots();
        btn.classList.add("is-active");
        playTone(tones[opt] || 500);
        setTimeout(() => btn.classList.remove("is-active"), 150);
      });
      grid.appendChild(btn);
      buttonsMap.set(opt, btn);
    });

    const playSeqBtn = document.createElement("button");
    playSeqBtn.className = "puzzle-btn ghost";
    playSeqBtn.textContent = "Reproducir patrón";
    playSeqBtn.addEventListener("click", () => {
      if (playingBack) return;
      playingBack = true;
      dom.message.textContent = "Escucha y repite...";
      let idx = 0;
      const interval = setInterval(() => {
        if (idx >= sequence.length) {
          clearInterval(interval);
          playingBack = false;
          dom.message.textContent = "";
          return;
        }
        const key = sequence[idx];
        const btn = buttonsMap.get(key);
        if (btn) {
          btn.classList.add("is-active");
          playTone(tones[key] || 500, 0.3);
          setTimeout(() => btn.classList.remove("is-active"), 200);
        }
        idx += 1;
      }, 450);
    });

    dom.content.appendChild(grid);
    dom.content.appendChild(playSeqBtn);

    dom.checkBtn.onclick = () => {
      attempt += 1;
      if (currentInput.length !== sequence.length) {
        dom.message.textContent = "Patrón incompleto.";
        dom.message.style.color = "#ffb3b3";
        return;
      }
      const ok = sequence.every((val, idx) => val === currentInput[idx]);
      if (ok) {
        dom.message.textContent = "Patrón correcto.";
        dom.message.style.color = "#3cff3c";
        dom.continueBtn.style.display = mergedConfig.successNext ? "inline-flex" : "none";
        if (mergedConfig.successNext && onSuccess) {
          dom.continueBtn.onclick = () => onSuccess(mergedConfig.successNext);
        }
      } else {
        if (attempt >= maxAttempts) {
          dom.message.textContent = mergedConfig.failText || "Has agotado los intentos.";
          dom.message.style.color = "#ffb3b3";
          dom.continueBtn.style.display = "none";
        } else {
          dom.message.textContent = `Patrón incorrecto. Intento ${attempt}/${maxAttempts}.`;
          dom.message.style.color = "#ffb3b3";
        }
        currentInput = [];
        renderDots();
      }
    };

    dom.resetBtn.onclick = () => {
      attempt = 0;
      currentInput = [];
      dom.message.textContent = "";
      dom.continueBtn.style.display = "none";
    };

    dom.message.textContent = "";
    dom.message.style.color = "#ffb3b3";
    dom.content.appendChild(grid);
    dom.content.appendChild(playSeqBtn);
  };

  const renderJigsaw = (mergedConfig, onSuccess) => {
    const { rows = 3, cols = 3, image } = mergedConfig.data || {};
    if (!image) {
      dom.content.innerHTML = "No se encontró la imagen del puzzle.";
      return;
    }

    const total = rows * cols;
    const positions = Array.from({ length: total }, (_, i) => i);
    const shuffled = [...positions].sort(() => Math.random() - 0.5);
    current = { type: "jigsaw", shuffled, rows, cols, mergedConfig };

    dom.content.innerHTML = "";
    const grid = document.createElement("div");
    grid.className = "puzzle-jigsaw-grid";
    grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    grid.style.gridTemplateRows = `repeat(${rows}, 1fr)`;

    let firstSelected = null;

    const renderTiles = () => {
      grid.innerHTML = "";
      shuffled.forEach((pos, idx) => {
        const tile = document.createElement("div");
        tile.className = "puzzle-jigsaw-tile";
        if (firstSelected === idx) tile.classList.add("selected");
        const x = pos % cols;
        const y = Math.floor(pos / cols);
        const bgX = (x / (cols - 1)) * 100;
        const bgY = (y / (rows - 1)) * 100;
        tile.style.backgroundImage = `url(${image})`;
        tile.style.backgroundPosition = `${bgX}% ${bgY}%`;
        tile.style.backgroundSize = `${cols * 100}% ${rows * 100}%`;
        tile.addEventListener("click", () => {
          if (firstSelected === null) {
            firstSelected = idx;
          } else {
            const tmp = shuffled[idx];
            shuffled[idx] = shuffled[firstSelected];
            shuffled[firstSelected] = tmp;
            firstSelected = null;
            checkSolved();
          }
          renderTiles();
        });
        grid.appendChild(tile);
      });
    };

    const checkSolved = () => {
      const solved = shuffled.every((pos, idx) => pos === idx);
      if (solved) {
        dom.message.textContent = "Puzzle completado.";
        dom.message.style.color = "#3cff3c";
        dom.continueBtn.style.display = mergedConfig.successNext ? "inline-flex" : "none";
        if (mergedConfig.successNext && onSuccess) {
          dom.continueBtn.onclick = () => onSuccess(mergedConfig.successNext);
        }
      } else {
        dom.message.textContent = "";
        dom.continueBtn.style.display = "none";
      }
    };

    dom.checkBtn.onclick = checkSolved;
    dom.resetBtn.onclick = () => {
      shuffled.splice(0, shuffled.length, ...positions.sort(() => Math.random() - 0.5));
      firstSelected = null;
      dom.message.textContent = "";
      dom.continueBtn.style.display = "none";
      renderTiles();
    };

    renderTiles();
    dom.content.appendChild(grid);
  };

  const render = (sceneId, puzzleConfig, onSuccess) => {
    if (!puzzleConfig) {
      hide();
      return;
    }
    openModal();
    dom.title.textContent = puzzleConfig.title || "Reto activo";
    dom.hint.textContent = puzzleConfig.data?.hint || puzzleConfig.description || "";
    dom.description.textContent = puzzleConfig.description || "Resuelve el reto para continuar.";
    dom.message.textContent = "";
    dom.message.style.color = "#ffb3b3";
    dom.continueBtn.style.display = "none";
    dom.continueBtn.onclick = null;

    switch (puzzleConfig.type) {
      case "sorting":
        renderSorting(puzzleConfig, onSuccess);
        break;
      case "jigsaw":
        renderJigsaw(puzzleConfig, onSuccess);
        break;
      case "pattern":
        renderPattern(puzzleConfig, onSuccess);
        break;
      default:
        dom.content.innerHTML = "Puzzle no interactivo aún.";
        dom.checkBtn.onclick = null;
        dom.resetBtn.onclick = null;
        if (puzzleConfig.successNext) {
          dom.continueBtn.style.display = "inline-flex";
          dom.continueBtn.onclick = () => onSuccess && onSuccess(puzzleConfig.successNext);
        }
        break;
    }
  };

  dom.closeBtn.addEventListener("click", hide);
  dom.backdrop.addEventListener("click", hide);

  return { render, hide };
}
