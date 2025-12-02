export function createPuzzleManager(dom) {
  let current = null;

  const hide = () => {
    dom.panel.style.display = "none";
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

  const render = (sceneId, puzzleConfig, onSuccess) => {
    if (!puzzleConfig) {
      hide();
      return;
    }
    dom.panel.style.display = "block";
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

  return { render, hide };
}
